"""Ingeniería de features del modelo de demanda.

Un único lugar para construir el dataset diario y sus features, importado tanto
por los notebooks (`01_data`, `02_procesos`, `03_resultados`) como por la API
(`practica3.api.main`), para no duplicar la lógica en dos sitios.

Fuente de datos: `data/raw/ventas.csv`, la exportación real de ventas de **El Café
que te Conté** (nivel ticket/línea, 2026-04-01 a 2026-07-31). Reemplaza al dataset
sintético usado en la primera iteración de esta práctica. Con datos reales ya no se
fabrican variables sin respaldo: se **retiraron** `proporcion_stock` (no hay
inventario en este export), `promocion_activa` y `clima_lluvia` (no hay esas
columnas en el CSV), y se **agregaron** tres variables genuinamente reales que el
export sí trae: `precio_promedio` (precio unitario real), `n_tickets_dia` (tráfico
de clientes real, no estimado) y `hora_promedio_venta` (patrón horario real).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# ── Features ──────────────────────────────────────────────────────────────────
# Calendario + historia temporal (heredadas de la iteración sintética; sin
# `proporcion_stock`, que dependía de un inventario que este export no trae).
BASE_FEATURES = [
    "cantidad_vendida", "dia_semana", "mes", "es_weekend", "es_feriado",
    "dias_desde_inicio", "categoria_encoded",
    "lag_1", "lag_7", "rolling_mean_7", "rolling_std_7",
]

# Más historia, codificación cíclica y las 3 variables reales nuevas
# (`precio_promedio`, `n_tickets_dia`, `hora_promedio_venta`) que reemplazan a las
# sintéticas de la iteración anterior (`promocion_activa`, `clima_lluvia`,
# `flujo_clientes_estimado`).
NEW_FEATURES = [
    "lag_2", "lag_14", "rolling_mean_14", "rolling_std_14",
    "dia_semana_sin", "dia_semana_cos", "mes_sin", "mes_cos",
    "es_fecha_especial", "temporada_seca",
    "precio_promedio", "n_tickets_dia", "hora_promedio_venta",
]

FEATURE_COLS = BASE_FEATURES + NEW_FEATURES

HORIZONTES = (1, 3, 7)

# Calendario Ecuador dentro del rango real de datos (2026-04-01 a 2026-07-31).
# Viernes Santo movible (Pascua 2026 = 5 abr), Día del Trabajo, Batalla de Pichincha.
FERIADOS_NACIONALES = ["2026-04-03", "2026-05-01", "2026-05-24"]
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
    "categoria_encoded": "La categoría del producto",
    "lag_1": "Cuánto se vendió ayer",
    "lag_2": "Cuánto se vendió hace 2 días",
    "lag_7": "Cuánto se vendió hace una semana",
    "lag_14": "Cuánto se vendió hace dos semanas",
    "rolling_mean_7": "El promedio de ventas de la última semana",
    "rolling_std_7": "Qué tan irregulares fueron las ventas la última semana",
    "rolling_mean_14": "El promedio de ventas de las últimas dos semanas",
    "rolling_std_14": "Qué tan irregulares fueron las ventas las últimas dos semanas",
    "es_fecha_especial": "Si es una fecha especial (ej. Día de la Madre)",
    "temporada_seca": "La temporada del año (seca o lluviosa)",
    "precio_promedio": "El precio promedio del producto ese día",
    "n_tickets_dia": "Cuántos clientes visitaron la cafetería ese día",
    "hora_promedio_venta": "A qué hora del día se suele vender",
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


def cargar_datos_crudos(data_dir: Path) -> pd.DataFrame:
    """Carga `ventas.csv` (nivel ticket/línea) desde `data_dir`."""
    ventas = pd.read_csv(data_dir / "ventas.csv")
    ventas["fecha"] = pd.to_datetime(ventas["fecha_completa"], format="%d/%m/%Y")
    return ventas


def construir_dataset_diario(ventas: pd.DataFrame) -> pd.DataFrame:
    """Agrega ventas por (fecha, producto) y calcula todas las features de FEATURE_COLS.

    La granularidad es `producto` (33 items), no `producto + variante_o_sabor`
    (47 combos): menos disperso por serie temporal, más robusto para el modelo.
    """
    agg = (
        ventas.groupby(["fecha", "producto"])
        .agg(
            categoria=("categoria", "first"),
            cantidad_vendida=("cantidad_vendida", "sum"),
            precio_promedio=("precio_unitario", "mean"),
        )
        .reset_index()
    )

    # n_tickets_dia: tráfico de clientes REAL (tickets distintos ese día),
    # a nivel de todo el negocio — mismo valor para todos los productos del día.
    tickets_dia = ventas.groupby("fecha")["id_ticket"].nunique().rename("n_tickets_dia")
    agg = agg.merge(tickets_dia, on="fecha", how="left")

    # hora_promedio_venta: hora del día (0-24, fraccionaria) en que se vendió
    # ese producto, promediada sobre todas sus ventas del día.
    horas = pd.to_datetime(ventas["hora_exacta"], format="%H:%M")
    ventas = ventas.assign(hora=horas.dt.hour + horas.dt.minute / 60)
    hora_prom = ventas.groupby(["fecha", "producto"])["hora"].mean().rename("hora_promedio_venta")
    agg = agg.merge(hora_prom, on=["fecha", "producto"], how="left")

    # product_id estable: entero asignado por orden alfabético del nombre real.
    productos_ordenados = sorted(agg["producto"].unique())
    producto_a_id = {p: i + 1 for i, p in enumerate(productos_ordenados)}
    agg["product_id"] = agg["producto"].map(producto_a_id)
    df = agg.rename(columns={"producto": "nombre"}).sort_values(["product_id", "fecha"]).reset_index(drop=True)

    # ── calendario base ──────────────────────────────────────────────────────
    df["dia_semana"] = df["fecha"].dt.weekday
    df["mes"] = df["fecha"].dt.month
    df["es_weekend"] = (df["dia_semana"] >= 5).astype(int)
    df["es_feriado"] = df["fecha"].isin(pd.to_datetime(FERIADOS_NACIONALES)).astype(int)
    df["dias_desde_inicio"] = (df["fecha"] - df["fecha"].min()).dt.days
    df["categoria_encoded"] = LabelEncoder().fit_transform(df["categoria"])

    # ── calendario extendido (Feedback Empresas §IV.A) ──────────────────────
    df["es_fecha_especial"] = df["fecha"].isin(pd.to_datetime(FECHAS_ESPECIALES)).astype(int)
    # Sierra ecuatoriana: jun-sep es la temporada seca ("verano austral").
    df["temporada_seca"] = df["mes"].between(6, 9).astype(int)

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
