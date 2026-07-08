"""Tests de src/practica3/features.py con un dataset sintético pequeño y controlado."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from practica3.features import (
    FEATURE_COLS,
    HORIZONTES,
    agregar_targets,
    calidad_datos_por_producto,
    construir_dataset_diario,
    split_temporal,
)


@pytest.fixture
def inventory():
    return pd.DataFrame({
        "product_id": [1, 2],
        "nombre": ["Producto A", "Producto B"],
        "categoria": ["Electronica", "Accesorios"],
    })


@pytest.fixture
def sales():
    fechas = pd.date_range("2026-01-01", periods=40, freq="D")
    filas = []
    rng = np.random.default_rng(0)
    for pid in (1, 2):
        for fecha in fechas:
            filas.append({
                "product_id": pid,
                "nombre": f"Producto {pid}",
                "fecha_venta": fecha,
                "cantidad_vendida": int(rng.integers(1, 20)),
                "stock_en_momento": int(rng.integers(50, 300)),
            })
    return pd.DataFrame(filas)


def test_construir_dataset_diario_tiene_todas_las_features(sales, inventory):
    df = construir_dataset_diario(sales, inventory)
    faltantes = set(FEATURE_COLS) - set(df.columns)
    assert not faltantes, f"Features faltantes: {faltantes}"


def test_lag_1_no_mira_el_futuro(sales, inventory):
    df = construir_dataset_diario(sales, inventory).sort_values(["product_id", "fecha"])
    producto1 = df[df["product_id"] == 1].reset_index(drop=True)
    # lag_1 de la fila i debe ser exactamente cantidad_vendida de la fila i-1
    for i in range(1, len(producto1)):
        assert producto1.loc[i, "lag_1"] == producto1.loc[i - 1, "cantidad_vendida"]


def test_agregar_targets_desplaza_hacia_el_futuro(sales, inventory):
    df = construir_dataset_diario(sales, inventory)
    df = agregar_targets(df, HORIZONTES)
    producto1 = df[df["product_id"] == 1].sort_values("fecha").reset_index(drop=True)
    for h in HORIZONTES:
        col = f"target_h{h}"
        for i in range(len(producto1) - h):
            assert producto1.loc[i, col] == producto1.loc[i + h, "cantidad_vendida"]


def test_split_temporal_no_mezcla_fechas(sales, inventory):
    df = construir_dataset_diario(sales, inventory)
    df = agregar_targets(df, HORIZONTES)
    train, test, corte = split_temporal(df, target_col="target_h1")
    assert train["fecha"].max() <= corte
    assert test["fecha"].min() > corte
    assert len(train) > 0 and len(test) > 0


def test_calidad_datos_marca_historico_insuficiente(sales, inventory):
    df = construir_dataset_diario(sales, inventory)
    resumen = calidad_datos_por_producto(df, minimo=1000)
    assert not resumen["calidad_suficiente"].any()

    resumen_bajo = calidad_datos_por_producto(df, minimo=1)
    assert resumen_bajo["calidad_suficiente"].all()
