"""Reentrenamiento incremental a partir de un CSV de ventas nuevo.

Agrega filas nuevas a `data/raw/ventas.csv` (con backup del archivo anterior) y
reajusta los mismos modelos que ya existen — SVR (h1/h3/h7), SVC de alerta e
IsolationForest — a los datos actualizados.

Deliberadamente NO repite el `GridSearchCV` del notebook 2 (búsqueda de
hiperparámetros): reutiliza los ya encontrados (`models/metadata.json ->
mejores_hiperparametros`), así el reentrenamiento responde en segundos desde un
botón de la beta, no minutos. Es un refresco de pesos a datos nuevos, no una
repetición del proceso de investigación completo.
"""

from __future__ import annotations

import io
import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.ensemble import IsolationForest
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, SVR

from .features import HORIZONTES, agregar_targets, construir_dataset_diario, split_temporal

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
MODELS_DIR = ROOT_DIR / "models"
METRICS_PATH = ROOT_DIR / "metrics" / "metrics.json"
VENTAS_PATH = DATA_RAW_DIR / "ventas.csv"

COLUMNAS_VENTAS = [
    "id_ticket",
    "fecha_completa",
    "hora_exacta",
    "dia_de_la_semana",
    "mes",
    "categoria",
    "producto",
    "variante_o_sabor",
    "cantidad_vendida",
    "precio_unitario",
    "total_linea",
]

RNG = 42


class ReentrenamientoError(ValueError):
    """CSV inválido o sin filas nuevas — no bloquea al usuario con un 500, es un 400 claro."""


def _cargar_y_validar_csv(contenido_csv: bytes) -> pd.DataFrame:
    try:
        nuevas = pd.read_csv(io.BytesIO(contenido_csv))
    except Exception as exc:  # noqa: BLE001 - cualquier fallo de parseo es un error de usuario
        raise ReentrenamientoError(f"No se pudo leer el CSV: {exc}") from exc

    faltantes = [c for c in COLUMNAS_VENTAS if c not in nuevas.columns]
    if faltantes:
        raise ReentrenamientoError(
            f"El CSV no tiene el esquema de ventas.csv — faltan columnas: {faltantes}"
        )
    nuevas = nuevas[COLUMNAS_VENTAS]
    if nuevas.empty:
        raise ReentrenamientoError("El CSV no tiene filas.")

    # Todo lo que después se parsea se valida acá, antes de tocar el histórico:
    # un error a mitad del reentrenamiento dejaba ventas.csv ya sobrescrito.
    _exigir(
        nuevas,
        pd.to_datetime(nuevas["fecha_completa"], format="%d/%m/%Y", errors="coerce").notna(),
        "fecha_completa no tiene el formato dd/mm/aaaa",
    )
    _exigir(
        nuevas,
        pd.to_datetime(nuevas["hora_exacta"], format="%H:%M", errors="coerce").notna(),
        "hora_exacta no tiene el formato hh:mm",
    )
    cantidad = pd.to_numeric(nuevas["cantidad_vendida"], errors="coerce")
    precio = pd.to_numeric(nuevas["precio_unitario"], errors="coerce")
    _exigir(nuevas, cantidad > 0, "cantidad_vendida debe ser un número mayor que 0")
    _exigir(nuevas, precio >= 0, "precio_unitario debe ser un número no negativo")
    _exigir(
        nuevas,
        nuevas["producto"].notna() & nuevas["categoria"].notna(),
        "producto y categoria no pueden estar vacíos",
    )
    return nuevas


def _exigir(df: pd.DataFrame, ok: pd.Series, mensaje: str) -> None:
    if not ok.all():
        filas = (df.index[~ok][:5] + 2).tolist()  # +2: encabezado y numeración desde 1
        raise ReentrenamientoError(f"{mensaje} (filas {filas} del CSV).")


def _escribir_atomico(path: Path, contenido: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(contenido)
    os.replace(tmp, path)


def reentrenar_con_csv(contenido_csv: bytes) -> dict:
    nuevas = _cargar_y_validar_csv(contenido_csv)
    actuales = pd.read_csv(VENTAS_PATH)

    combinado = pd.concat([actuales, nuevas], ignore_index=True)
    combinado = combinado.drop_duplicates(
        subset=["id_ticket", "producto", "variante_o_sabor"], keep="first"
    )
    filas_nuevas = len(combinado) - len(actuales)
    if filas_nuevas <= 0:
        raise ReentrenamientoError(
            "El CSV no aportó filas nuevas (todas las filas ya existían en el histórico)."
        )

    ventas = combinado.copy()
    ventas["fecha"] = pd.to_datetime(ventas["fecha_completa"], format="%d/%m/%Y")
    df = agregar_targets(construir_dataset_diario(ventas))

    metadata = json.loads((MODELS_DIR / "metadata.json").read_text())
    feature_cols_svr = metadata["feature_cols_svr"]
    feature_cols_svc_iso = metadata["feature_cols_svc_iso"]
    hparams = metadata["mejores_hiperparametros"]

    # Se entrena todo en memoria; nada se escribe a disco hasta el final.
    artefactos: dict[str, object] = {}
    metricas: dict[str, dict] = {}
    residuales: dict[str, dict] = {}
    test_h1, pred_h1, pipe_h1 = None, None, None

    for h in HORIZONTES:
        train, test, _ = split_temporal(df, f"target_h{h}", feature_cols_svr)
        X_train, y_train = train[feature_cols_svr].values, train[f"target_h{h}"].values
        X_test, y_test = test[feature_cols_svr].values, test[f"target_h{h}"].values

        p = hparams[str(h)]
        pipe = Pipeline(
            [
                ("sc", StandardScaler()),
                (
                    "svr",
                    SVR(
                        kernel=p["svr__kernel"],
                        C=p["svr__C"],
                        gamma=p["svr__gamma"],
                        epsilon=p["svr__epsilon"],
                    ),
                ),
            ]
        )
        pipe.fit(X_train, y_train)
        pred_test = pipe.predict(X_test)

        metricas[str(h)] = {
            "rmse": round(float(mean_squared_error(y_test, pred_test) ** 0.5), 4),
            "mae": round(float(mean_absolute_error(y_test, pred_test)), 4),
            "r2": round(float(r2_score(y_test, pred_test)), 4),
        }
        p10, p50, p90 = np.quantile(y_test - pred_test, [0.10, 0.50, 0.90])
        residuales[str(h)] = {
            "p10": round(float(p10), 3),
            "p50": round(float(p50), 3),
            "p90": round(float(p90), 3),
        }

        artefactos[f"svr_h{h}.joblib"] = pipe
        if h == 1:
            test_h1, pred_h1, pipe_h1 = test.copy(), pred_test, pipe

    assert test_h1 is not None and pred_h1 is not None and pipe_h1 is not None

    # SVC de alerta de alta demanda + IsolationForest (t+1), mismo diseño del notebook 2
    train_clf, test_clf, _ = split_temporal(df, "target_h1", feature_cols_svc_iso)
    umbral = train_clf.groupby("product_id")["target_h1"].quantile(0.75)
    y_train_clf = (
        train_clf["target_h1"].values > train_clf["product_id"].map(umbral).values
    ).astype(int)
    y_test_clf = (test_clf["target_h1"].values > test_clf["product_id"].map(umbral).values).astype(
        int
    )
    X_train_clf = train_clf[feature_cols_svc_iso].values
    X_test_clf = test_clf[feature_cols_svc_iso].values

    svc_alerta = Pipeline(
        [
            ("sc", StandardScaler()),
            (
                "svc",
                SVC(
                    kernel="rbf",
                    C=10,
                    gamma="scale",
                    class_weight="balanced",
                    probability=True,
                    random_state=RNG,
                ),
            ),
        ]
    )
    svc_alerta.fit(X_train_clf, y_train_clf)
    auc = roc_auc_score(y_test_clf, svc_alerta.predict_proba(X_test_clf)[:, 1])
    artefactos["svc_alerta.joblib"] = svc_alerta

    isolation_forest = IsolationForest(
        n_estimators=200, contamination=0.05, random_state=RNG, n_jobs=1
    )
    isolation_forest.fit(X_train_clf)
    n_anomalias = int((isolation_forest.predict(X_test_clf) == -1).sum())
    artefactos["isolation_forest.joblib"] = isolation_forest

    # Métrica de negocio (ingresos en riesgo t+1) — mismo cálculo del notebook 3
    precio_por_producto = df.groupby("product_id")["precio_promedio"].mean()
    test_h1["pred"] = pred_h1
    test_h1["pred_naive"] = test_h1["lag_7"]
    test_h1["precio"] = test_h1["product_id"].map(precio_por_producto)

    def _en_riesgo(col_pred: str) -> float:
        quiebre = (test_h1["target_h1"] - test_h1[col_pred]).clip(lower=0) * test_h1["precio"]
        sobrante = (test_h1[col_pred] - test_h1["target_h1"]).clip(lower=0) * test_h1["precio"]
        return float(quiebre.sum() + sobrante.sum())

    total_modelo = _en_riesgo("pred")
    total_naive = _en_riesgo("pred_naive")
    reduccion_pct = round(100 * (1 - total_modelo / total_naive), 2) if total_naive else 0.0

    # Importancia de variables (permutation, recalculada con menos repeticiones que el
    # notebook original para que el reentrenamiento siga siendo rápido)
    imp = permutation_importance(
        pipe_h1,
        test_h1[feature_cols_svr].values,
        test_h1["target_h1"].values,
        n_repeats=10,
        random_state=RNG,
        n_jobs=1,
    )
    importancia = pd.Series(imp.importances_mean, index=feature_cols_svr).sort_values(
        ascending=False
    )

    ahora = datetime.now()
    rango_fechas = f"{df['fecha'].min().date()} a {df['fecha'].max().date()}"

    metadata["metricas"] = metricas
    metadata["svc_alerta"] = {"roc_auc_test": round(float(auc), 4)}
    metadata["isolation_forest"] = {"contamination": 0.05, "n_anomalias_test": n_anomalias}
    metadata["importancia_variables_finales"] = importancia.round(4).to_dict()
    metadata["fuente_datos"] = f"ventas.csv real (El Café que te Conté), {rango_fechas}"
    metadata["ultimo_reentrenamiento"] = {
        "timestamp": ahora.isoformat(timespec="seconds"),
        "filas_nuevas_agregadas": int(filas_nuevas),
        "filas_totales_ventas": int(len(combinado)),
        "nota": (
            "Hiperparámetros reutilizados de la búsqueda original (GridSearchCV) — no re-buscados."
        ),
    }

    metrics_json = json.loads(METRICS_PATH.read_text())
    metrics_json["generado_en"] = ahora.isoformat(timespec="seconds")
    metrics_json["dataset"]["origen"] = f"real (ventas.csv, El Café que te Conté, {rango_fechas})"
    metrics_json["dataset"]["n_productos"] = int(df["product_id"].nunique())
    metrics_json["dataset"]["n_dias"] = int(df["fecha"].nunique())
    metrics_json["metricas_tecnicas_por_horizonte"] = metricas
    metrics_json["clasificador_alerta_alta_demanda"] = {"roc_auc_test": round(float(auc), 4)}
    metrics_json["deteccion_anomalias"] = {
        "contamination": 0.05,
        "n_anomalias_test": n_anomalias,
        "pct_anomalias_test": round(n_anomalias / len(test_clf), 4),
    }
    metrics_json["metricas_negocio_t1"] = {
        "ingresos_en_riesgo_baseline_ingenuo": round(total_naive, 2),
        "ingresos_en_riesgo_modelo": round(total_modelo, 2),
        "reduccion_pct": reduccion_pct,
        "nota": "precio_unitario real, sin márgenes inventados — recalculado tras reentrenamiento.",
    }
    metrics_json["importancia_variables_top5"] = importancia.head(5).round(4).to_dict()

    # Persistencia: respaldo, histórico nuevo y artefactos, recién ahora.
    backup_path = DATA_RAW_DIR / f"ventas_backup_{ahora:%Y%m%d_%H%M%S}.csv"
    actuales.to_csv(backup_path, index=False)
    _escribir_atomico(VENTAS_PATH, combinado.to_csv(index=False))
    for nombre, modelo in artefactos.items():
        tmp = MODELS_DIR / f"{nombre}.tmp"
        dump(modelo, tmp)
        os.replace(tmp, MODELS_DIR / nombre)
    _escribir_atomico(
        MODELS_DIR / "metadata.json", json.dumps(metadata, indent=2, ensure_ascii=False)
    )
    _escribir_atomico(MODELS_DIR / "residuales.json", json.dumps(residuales, indent=2))
    _escribir_atomico(METRICS_PATH, json.dumps(metrics_json, indent=2, ensure_ascii=False))

    return {
        "filas_nuevas_agregadas": int(filas_nuevas),
        "filas_totales_ventas": int(len(combinado)),
        "rango_fechas": rango_fechas,
        "metricas": metricas,
        "reduccion_pct_ingresos_riesgo": reduccion_pct,
        "backup_creado": backup_path.name,
        "nota": (
            "Hiperparámetros reutilizados (no re-buscados) — reentrenamiento rápido sobre "
            "datos actualizados."
        ),
    }
