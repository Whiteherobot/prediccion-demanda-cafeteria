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
(AUC del SVC bajaba de 0.62 a 0.57) — por eso SVC/IsolationForest usan las
features candidatas completas.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap

from .features import (
    FEATURE_LABELS_NEGOCIO,
    HORIZONTES,
    calidad_datos_por_producto,
    cargar_datos_crudos,
    construir_dataset_diario,
)

ROOT_DIR = Path(__file__).resolve().parents[2]
MODELS_DIR = ROOT_DIR / "models"
DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
METRICS_PATH = ROOT_DIR / "metrics" / "metrics.json"
SHAP_BACKGROUND_SIZE = 50
SHAP_NSAMPLES = 200


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

        # Explicadores SHAP: caros de construir (background + kernel), se arman una
        # sola vez por horizonte, la primera vez que se piden (no en el arranque).
        self._shap_background = (
            self.df[self.feature_cols_svr]
            .dropna()
            .sample(n=min(SHAP_BACKGROUND_SIZE, len(self.df)), random_state=42)
        )
        self._explainers: dict[int, shap.KernelExplainer] = {}

    def info_modelo(self) -> dict:
        # Peor caso entre productos: la fecha a partir de la cual TODOS tienen fila
        # de referencia válida (rolling_mean_14 necesita 14 días previos por producto).
        validas = self.df.dropna(subset=self.feature_cols_svr)
        min_valido_referencia = validas.groupby("product_id")["fecha"].min().max()
        return {
            "features_svr": self.feature_cols_svr,
            "features_svc_iso": self.feature_cols_svc_iso,
            "horizontes_soportados": list(HORIZONTES),
            "metricas": self.metadata.get("metricas", {}),
            "calidad_datos_por_producto": {
                int(pid): bool(ok) for pid, ok in self.calidad_por_producto.items()
            },
            "rango_fechas": {
                "min": str(self.df["fecha"].min().date()),
                "max": str(self.df["fecha"].max().date()),
                "min_valido_referencia": str(min_valido_referencia.date()),
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

    def metricas_negocio(self) -> dict:
        """Impacto de negocio real (t+1) y factores globales, desde `metrics/metrics.json`
        (generado por el notebook 3 — no se recalcula acá, solo se sirve)."""
        metrics = json.loads(METRICS_PATH.read_text())
        negocio = metrics["metricas_negocio_t1"]
        return {
            "ingresos_en_riesgo_baseline_ingenuo": negocio["ingresos_en_riesgo_baseline_ingenuo"],
            "ingresos_en_riesgo_modelo": negocio["ingresos_en_riesgo_modelo"],
            "reduccion_pct": negocio["reduccion_pct"],
            "importancia_variables_top5": metrics["importancia_variables_top5"],
        }

    def reporte_demanda(self, fecha: str) -> dict:
        """Reporte conciso de qué producto va a necesitar más preparación:
        - `proyeccion_7dias`: predicción real del SVR a horizonte t+7 (el modelo no
          predice más allá de 7 días, así que "fin de semana" es literalmente eso).
        - `historico_30dias`: suma de ventas REALES (no una proyección — el modelo
          no tiene horizonte a 30 días) de los últimos 30 días hasta `fecha`, como
          proxy de qué se necesitará más "de cara al mes" basado en tendencia real.
        """
        fecha_ts = pd.Timestamp(fecha)
        nombres = dict(zip(self.df["product_id"], self.df["nombre"], strict=False))

        items = []
        for pid in sorted(nombres):
            try:
                pred7 = self.predecir(int(pid), fecha, horizonte=7)["prediccion_esperada"]
            except ValueError:
                pred7 = None

            ventana = self.df[
                (self.df["product_id"] == pid)
                & (self.df["fecha"] > fecha_ts - pd.Timedelta(days=30))
                & (self.df["fecha"] <= fecha_ts)
            ]
            items.append(
                {
                    "product_id": int(pid),
                    "nombre": nombres[pid],
                    "proyeccion_7dias": round(pred7, 2) if pred7 is not None else None,
                    "historico_30dias": round(float(ventana["cantidad_vendida"].sum()), 2),
                }
            )

        con_proyeccion = [i for i in items if i["proyeccion_7dias"] is not None]
        top_semana = max(con_proyeccion, key=lambda i: i["proyeccion_7dias"]) if con_proyeccion else None
        top_mes = max(items, key=lambda i: i["historico_30dias"])

        return {
            "fecha_referencia": str(fecha_ts.date()),
            "top_semana": top_semana,
            "top_mes": top_mes,
            "items": sorted(items, key=lambda i: i["historico_30dias"], reverse=True),
        }

    def _explainer(self, horizonte: int) -> shap.KernelExplainer:
        if horizonte not in self._explainers:
            self._explainers[horizonte] = shap.KernelExplainer(
                self.svr[horizonte].predict, self._shap_background
            )
        return self._explainers[horizonte]

    def explicar(self, product_id: int, fecha: str, horizonte: int = 1) -> dict:
        """Explicación local (Kernel SHAP) de una predicción puntual — mismo patrón que
        `notebooks/03_resultados.ipynb` secciones 8-9, servido on-demand para un solo
        producto/fecha (no se precalculan los 33, sería demasiado lento)."""
        if horizonte not in self.svr:
            raise ValueError(f"Horizonte no soportado: {horizonte}. Use uno de {HORIZONTES}")

        fila = self._fila_referencia(product_id, fecha, self.feature_cols_svr)
        X = fila[self.feature_cols_svr].to_frame().T.astype(float)

        pred = float(self.svr[horizonte].predict(X.values)[0])
        explainer = self._explainer(horizonte)
        shap_vals = explainer.shap_values(X, nsamples=SHAP_NSAMPLES, silent=True)[0]

        orden = np.argsort(-np.abs(shap_vals))[:5]
        factores = [
            {
                "concepto_negocio": FEATURE_LABELS_NEGOCIO.get(
                    self.feature_cols_svr[i], self.feature_cols_svr[i]
                ),
                "shap": round(float(shap_vals[i]), 3),
            }
            for i in orden
        ]

        return {
            "product_id": int(product_id),
            "fecha_referencia_datos": str(fila["fecha"].date()),
            "prediccion_h": round(pred, 2),
            "base_value": round(float(explainer.expected_value), 2),
            "factores": factores,
        }
