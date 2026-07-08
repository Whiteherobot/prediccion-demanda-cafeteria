"""Ingeniería de features del modelo de demanda.

Un único lugar para construir el dataset diario y sus features, importado tanto
por los notebooks (`01_data`, `02_procesos`, `03_resultados`) como por la API
(`practica3.api.main`), para no duplicar la lógica en dos sitios.

Reusa el dataset sintético de la Práctica 2 (`sales_history.csv` / `inventory.csv`)
y replica sus 12 features originales, ampliándolas con variables de calendario,
codificación cíclica y variables exógenas sintéticas pedidas en la retroalimentación
empresarial (`Feedback Empresas.pdf`, sección IV.A): promociones, fechas especiales,
temporada y clima. Como todavía no hay datos reales de la empresa, estas últimas se
generan de forma sintética y NO se correlacionan artificialmente con la demanda ya
generada en la Práctica 2 — así el análisis de importancia de variables (notebook 2)
reporta honestamente si aportan señal o no, en vez de simular un resultado.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# ── Features ──────────────────────────────────────────────────────────────────
# Las 12 originales de la Práctica 2 / Informe SVM.
BASE_FEATURES = [
    "cantidad_vendida", "dia_semana", "mes", "es_weekend", "es_feriado",
    "dias_desde_inicio", "proporcion_stock", "categoria_encoded",
    "lag_1", "lag_7", "rolling_mean_7", "rolling_std_7",
]

# Nuevas: más historia temporal, codificación cíclica y variables exógenas.
NEW_FEATURES = [
    "lag_2", "lag_14", "rolling_mean_14", "rolling_std_14",
    "dia_semana_sin", "dia_semana_cos", "mes_sin", "mes_cos",
    "es_fecha_especial", "temporada_seca",
    "promocion_activa", "clima_lluvia", "flujo_clientes_estimado",
]

FEATURE_COLS = BASE_FEATURES + NEW_FEATURES

HORIZONTES = (1, 3, 7)

# Calendario Ecuador dentro del rango de datos (2026-04-05 a 2026-10-01).
FERIADOS_NACIONALES = ["2026-05-01", "2026-05-24", "2026-08-10"]
# Fechas relevantes para un negocio local en Cuenca (café): fundación de la
# ciudad y día de la madre — no son feriado nacional pero mueven la afluencia.
FECHAS_ESPECIALES = ["2026-04-12", "2026-05-10"]

MIN_DIAS_HISTORICOS = 30  # umbral de calidad de datos por producto

# Traducción a lenguaje de negocio para reportes no técnicos (Feedback Empresas
# §V.6/V.7). Varias columnas técnicas describen el mismo concepto de negocio
# (ej. `dia_semana`, `dia_semana_sin`, `dia_semana_cos` son 3 formas de codificar
# "qué día de la semana es") — el reporte debe deduplicar por concepto, no listar
# las 3 variantes como si fueran factores distintos.
FEATURE_LABELS_NEGOCIO = {
    "cantidad_vendida": "Cuánto se vendió hoy",
    "dia_semana": "Qué día de la semana es",
    "dia_semana_sin": "Qué día de la semana es",
    "dia_semana_cos": "Qué día de la semana es",
    "mes": "El mes del año",
    "mes_sin": "El mes del año",
    "mes_cos": "El mes del año",
    "es_weekend": "Si es fin de semana",
    "es_feriado": "Si es feriado nacional",
    "dias_desde_inicio": "La tendencia general del negocio en el tiempo",
    "proporcion_stock": "Cuánto stock hay disponible",
    "categoria_encoded": "La categoría del producto",
    "lag_1": "Cuánto se vendió ayer",
    "lag_2": "Cuánto se vendió hace 2 días",
    "lag_7": "Cuánto se vendió hace una semana",
    "lag_14": "Cuánto se vendió hace dos semanas",
    "rolling_mean_7": "El promedio de ventas de la última semana",
    "rolling_std_7": "Qué tan irregulares fueron las ventas la última semana",
    "rolling_mean_14": "El promedio de ventas de las últimas dos semanas",
    "rolling_std_14": "Qué tan irregulares fueron las ventas las últimas dos semanas",
    "promocion_activa": "Si hay una promoción activa",
    "clima_lluvia": "Si está lloviendo",
    "flujo_clientes_estimado": "Cuántos clientes se esperan",
    "es_fecha_especial": "Si es una fecha especial (ej. Día de la Madre)",
    "temporada_seca": "La temporada del año (seca o lluviosa)",
}


def etiquetas_negocio_top_n(importancia_ordenada, n: int = 5) -> list[str]:
    """Traduce un ranking de features (más importante primero) a `n` conceptos de
    negocio únicos, saltando duplicados (ej. las 3 variantes de día de la semana
    cuentan como un solo concepto)."""
    vistas: list[str] = []
    for nombre in importancia_ordenada.index:
        etiqueta = FEATURE_LABELS_NEGOCIO.get(nombre, nombre)
        if etiqueta not in vistas:
            vistas.append(etiqueta)
        if len(vistas) == n:
            break
    return vistas


def cargar_datos_crudos(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Carga inventory.csv y sales_history.csv desde `data_dir`."""
    inventory = pd.read_csv(data_dir / "inventory.csv")
    sales = pd.read_csv(data_dir / "sales_history.csv", parse_dates=["fecha_venta"])
    return inventory, sales


def construir_dataset_diario(
    sales: pd.DataFrame, inventory: pd.DataFrame, seed: int = 42
) -> pd.DataFrame:
    """Agrega ventas por (fecha, producto) y calcula todas las features de FEATURE_COLS."""
    registros = []
    for (fecha, pid), g in sales.groupby(["fecha_venta", "product_id"]):
        registros.append({
            "fecha": fecha,
            "product_id": pid,
            "nombre": g["nombre"].iloc[0],
            "cantidad_vendida": g["cantidad_vendida"].sum(),
            "stock_promedio": g["stock_en_momento"].mean(),
        })
    df = pd.DataFrame(registros).sort_values(["product_id", "fecha"]).reset_index(drop=True)

    # ── calendario base (idéntico a Práctica 2 / Informe) ──────────────────
    df["dia_semana"] = df["fecha"].dt.weekday
    df["mes"] = df["fecha"].dt.month
    df["es_weekend"] = (df["dia_semana"] >= 5).astype(int)
    df["es_feriado"] = df["fecha"].isin(pd.to_datetime(FERIADOS_NACIONALES)).astype(int)
    df["dias_desde_inicio"] = (df["fecha"] - df["fecha"].min()).dt.days
    df["proporcion_stock"] = df["stock_promedio"] / (df["stock_promedio"].max() + 1)

    # ── categoría real desde inventory.csv (evita diccionario manual) ──────
    cat_por_producto = inventory.set_index("product_id")["categoria"]
    df["categoria"] = df["product_id"].map(cat_por_producto)
    df["categoria_encoded"] = LabelEncoder().fit_transform(df["categoria"])

    # ── calendario extendido (Feedback Empresas §IV.A) ──────────────────────
    df["es_fecha_especial"] = df["fecha"].isin(pd.to_datetime(FECHAS_ESPECIALES)).astype(int)
    # Sierra ecuatoriana: jun-sep es la temporada seca ("verano austral").
    df["temporada_seca"] = df["mes"].between(6, 9).astype(int)

    # ── variables exógenas sintéticas (sin Excel real todavía) ─────────────
    rng = np.random.default_rng(seed)
    n = len(df)
    df["promocion_activa"] = (rng.random(n) < 0.08).astype(int)
    prob_lluvia = np.where(df["temporada_seca"] == 1, 0.15, 0.55)
    df["clima_lluvia"] = (rng.random(n) < prob_lluvia).astype(int)
    flujo_base = 40 + 25 * df["es_weekend"] + 10 * df["es_feriado"]
    df["flujo_clientes_estimado"] = np.clip(flujo_base + rng.normal(0, 8, n), 5, None).round(1)

    # ── temporales, con shift(1) para no mirar el futuro ────────────────────
    grp = df.groupby("product_id")["cantidad_vendida"]
    df["lag_1"] = grp.shift(1)
    df["lag_2"] = grp.shift(2)
    df["lag_7"] = grp.shift(7)
    df["lag_14"] = grp.shift(14)
    df["rolling_mean_7"] = grp.transform(lambda x: x.shift(1).rolling(7).mean())
    df["rolling_std_7"] = grp.transform(lambda x: x.shift(1).rolling(7).std())
    df["rolling_mean_14"] = grp.transform(lambda x: x.shift(1).rolling(14).mean())
    df["rolling_std_14"] = grp.transform(lambda x: x.shift(1).rolling(14).std())

    # ── codificación cíclica: un kernel RBF ve distancias, no calendarios ──
    df["dia_semana_sin"] = np.sin(2 * np.pi * df["dia_semana"] / 7)
    df["dia_semana_cos"] = np.cos(2 * np.pi * df["dia_semana"] / 7)
    df["mes_sin"] = np.sin(2 * np.pi * df["mes"] / 12)
    df["mes_cos"] = np.cos(2 * np.pi * df["mes"] / 12)

    return df


def agregar_targets(df: pd.DataFrame, horizontes: tuple[int, ...] = HORIZONTES) -> pd.DataFrame:
    """Añade `target_h{h}` = demanda `h` días adelante, por producto."""
    df = df.copy()
    for h in horizontes:
        df[f"target_h{h}"] = df.groupby("product_id")["cantidad_vendida"].shift(-h)
    return df


def calidad_datos_por_producto(
    df: pd.DataFrame, minimo: int = MIN_DIAS_HISTORICOS
) -> pd.DataFrame:
    """Resumen de disponibilidad histórica por producto (Feedback Empresas §IV.C)."""
    resumen = (
        df.groupby("product_id")
        .agg(
            nombre=("nombre", "first"),
            n_dias=("fecha", "nunique"),
            fecha_min=("fecha", "min"),
            fecha_max=("fecha", "max"),
        )
        .reset_index()
    )
    resumen["calidad_suficiente"] = resumen["n_dias"] >= minimo
    return resumen


def split_temporal(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: list[str] | None = None,
    frac_train: float = 0.8,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    """División temporal 80/20 (sin fuga): train = fechas más antiguas, test = más recientes."""
    feature_cols = feature_cols or FEATURE_COLS
    df = df.dropna(subset=feature_cols + [target_col]).sort_values("fecha").reset_index(drop=True)
    corte = df["fecha"].quantile(frac_train)
    train = df[df["fecha"] <= corte].reset_index(drop=True)
    test = df[df["fecha"] > corte].reset_index(drop=True)
    return train, test, corte
