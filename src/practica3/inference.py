"""Carga de artefactos entrenados y predicción de demanda con intervalos y riesgo.

Usado tanto por el notebook 3 (resultados) como por la API. Los artefactos
(modelos SVR por horizonte, SVC de alerta, Isolation Forest, cuantiles de
residuos) se generan en el notebook 2 (`02_procesos.ipynb`) — este módulo solo
los carga y los sirve.

Nota de diseño: el SVR y el SVC/IsolationForest usan **conjuntos de features
distintos** (`feature_cols_svr` vs `feature_cols_svc_iso`). La selección de
features del notebook 2 se hace vía `permutation_importance` sobre el SVR — poda
features que no ayudan a predecir la cantidad exacta, pero esas mismas features sí
pueden ayudar a distinguir "día de alta demanda" o "contexto atípico" (tareas
distintas). Reusar el conjunto podado para las tres tareas midió empíricamente peor
(AUC del SVC caía a 0.47, peor que azar) — por eso SVC/IsolationForest usan las
features candidatas completas.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from .features import (
    HORIZONTES,
    calidad_datos_por_producto,
    cargar_datos_crudos,
    construir_dataset_diario,
)

ROOT_DIR = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT_DIR / "models"
DATA_RAW_DIR = ROOT_DIR / "data" / "raw"


class DemandPredictor:
    """Envuelve los modelos entrenados para servir predicciones de negocio."""

    def __init__(self, models_dir: Path = MODELS_DIR, data_raw_dir: Path = DATA_RAW_DIR):
        self.models_dir = models_dir

        self.svr = {h: joblib.load(models_dir / f"svr_h{h}.joblib") for h in HORIZONTES}
        self.svc_alerta = joblib.load(models_dir / "svc_alerta.joblib")
        self.isolation_forest = joblib.load(models_dir / "isolation_forest.joblib")
        self.residuales = json.loads((models_dir / "residuales.json").read_text())
        self.metadata = json.loads((models_dir / "metadata.json").read_text())
        # Dos conjuntos de features: el SVR usa el conjunto podado por
        # permutation_importance; el SVC/IsolationForest usan las candidatas
        # completas (ver nota de diseño arriba).
        self.feature_cols_svr = self.metadata["feature_cols_svr"]
        self.feature_cols_svc_iso = self.metadata["feature_cols_svc_iso"]

        ventas = cargar_datos_crudos(data_raw_dir)
        self.df = construir_dataset_diario(ventas)
        calidad = calidad_datos_por_producto(self.df)
        self.calidad_por_producto = dict(
            zip(calidad["product_id"], calidad["calidad_suficiente"])
        )

    def info_modelo(self) -> dict:
        return {
            "features_svr": self.feature_cols_svr,
            "features_svc_iso": self.feature_cols_svc_iso,
            "horizontes_soportados": list(HORIZONTES),
            "metricas": self.metadata.get("metricas", {}),
            "calidad_datos_por_producto": {
                int(pid): bool(ok) for pid, ok in self.calidad_por_producto.items()
            },
        }

    def _fila_referencia(self, product_id: int, fecha: str, feature_cols: list[str]) -> pd.Series:
        """Última fila con features completas para `product_id` en o antes de `fecha`."""
        fecha_ts = pd.Timestamp(fecha)
        hist = self.df[(self.df["product_id"] == product_id) & (self.df["fecha"] <= fecha_ts)]
        hist = hist.dropna(subset=feature_cols)
        if hist.empty:
            raise ValueError(
                f"Sin histórico suficiente para product_id={product_id} en o antes de {fecha}"
            )
        return hist.sort_values("fecha").iloc[-1]

    def predecir(self, product_id: int, fecha: str, horizonte: int = 1) -> dict:
        if horizonte not in self.svr:
            raise ValueError(f"Horizonte no soportado: {horizonte}. Use uno de {HORIZONTES}")

        fila_svr = self._fila_referencia(product_id, fecha, self.feature_cols_svr)
        X_svr = fila_svr[self.feature_cols_svr].to_frame().T.astype(float).to_numpy()

        fila_svc = self._fila_referencia(product_id, fecha, self.feature_cols_svc_iso)
        X_svc = fila_svc[self.feature_cols_svc_iso].to_frame().T.astype(float).to_numpy()

        punto = max(float(self.svr[horizonte].predict(X_svr)[0]), 0.0)
        q = self.residuales[str(horizonte)]  # cuantiles empíricos de residuos (test)
        esperado = max(punto + q["p50"], 0.0)
        conservador = max(punto + q["p10"], 0.0)
        optimista = max(punto + q["p90"], conservador)

        anomalia = bool(self.isolation_forest.predict(X_svc)[0] == -1)
        alerta_alta_demanda = bool(self.svc_alerta.predict(X_svc)[0] == 1)
        datos_suficientes = bool(self.calidad_por_producto.get(product_id, False))

        ancho_relativo = (optimista - conservador) / max(esperado, 1e-6)
        if not datos_suficientes or anomalia:
            riesgo = "rojo"
        elif ancho_relativo > 0.5:
            riesgo = "amarillo"
        else:
            riesgo = "verde"

        fecha_objetivo = fila_svr["fecha"] + pd.Timedelta(days=horizonte)

        return {
            "product_id": int(product_id),
            "fecha_solicitada": str(pd.Timestamp(fecha).date()),
            "fecha_referencia_datos": str(fila_svr["fecha"].date()),
            "fecha_objetivo": str(fecha_objetivo.date()),
            "horizonte_dias": horizonte,
            "prediccion_esperada": round(esperado, 2),
            "escenario_conservador": round(conservador, 2),
            "escenario_optimista": round(optimista, 2),
            "nivel_riesgo": riesgo,
            "alerta_alta_demanda": alerta_alta_demanda,
            "alerta_anomalia": anomalia,
            "datos_historicos_suficientes": datos_suficientes,
        }

    def predecir_alerta(self, product_id: int, fecha: str) -> dict:
        """Clasificación SVC standalone de alta demanda (horizonte t+1)."""
        fila = self._fila_referencia(product_id, fecha, self.feature_cols_svc_iso)
        X = fila[self.feature_cols_svc_iso].to_frame().T.astype(float).to_numpy()

        alerta = bool(self.svc_alerta.predict(X)[0] == 1)
        probabilidad = float(self.svc_alerta.predict_proba(X)[0, 1])

        return {
            "product_id": int(product_id),
            "fecha_solicitada": str(pd.Timestamp(fecha).date()),
            "fecha_referencia_datos": str(fila["fecha"].date()),
            "alerta_alta_demanda": alerta,
            "probabilidad": round(probabilidad, 4),
        }
