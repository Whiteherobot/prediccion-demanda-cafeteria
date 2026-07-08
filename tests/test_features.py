"""Tests de src/practica3/features.py con un dataset sintético pequeño y controlado
(mismo esquema que ventas.csv real: ticket/línea)."""

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
def ventas():
    fechas = pd.date_range("2026-01-01", periods=40, freq="D")
    productos = {"Café": "Bebidas", "Torta": "Pasteles"}
    rng = np.random.default_rng(0)
    filas = []
    ticket_id = 0
    for fecha in fechas:
        for hora in ["09:00", "14:30"]:
            ticket_id += 1
            for producto, categoria in productos.items():
                filas.append({
                    "id_ticket": f"T{ticket_id:05d}",
                    "fecha_completa": fecha.strftime("%d/%m/%Y"),
                    "hora_exacta": hora,
                    "dia_de_la_semana": fecha.day_name(),
                    "mes": fecha.month,
                    "categoria": categoria,
                    "producto": producto,
                    "variante_o_sabor": "N/A",
                    "cantidad_vendida": int(rng.integers(1, 20)),
                    "precio_unitario": 3.5 if producto == "Café" else 4.5,
                })
    df = pd.DataFrame(filas)
    df["total_linea"] = df["cantidad_vendida"] * df["precio_unitario"]
    df["fecha"] = pd.to_datetime(df["fecha_completa"], format="%d/%m/%Y")
    return df


def test_construir_dataset_diario_tiene_todas_las_features(ventas):
    df = construir_dataset_diario(ventas)
    faltantes = set(FEATURE_COLS) - set(df.columns)
    assert not faltantes, f"Features faltantes: {faltantes}"


def test_lag_1_no_mira_el_futuro(ventas):
    df = construir_dataset_diario(ventas).sort_values(["product_id", "fecha"])
    producto1 = df[df["product_id"] == df["product_id"].iloc[0]].reset_index(drop=True)
    # lag_1 de la fila i debe ser exactamente cantidad_vendida de la fila i-1
    for i in range(1, len(producto1)):
        assert producto1.loc[i, "lag_1"] == producto1.loc[i - 1, "cantidad_vendida"]


def test_agregar_targets_desplaza_hacia_el_futuro(ventas):
    df = construir_dataset_diario(ventas)
    df = agregar_targets(df, HORIZONTES)
    pid = df["product_id"].iloc[0]
    producto1 = df[df["product_id"] == pid].sort_values("fecha").reset_index(drop=True)
    for h in HORIZONTES:
        col = f"target_h{h}"
        for i in range(len(producto1) - h):
            assert producto1.loc[i, col] == producto1.loc[i + h, "cantidad_vendida"]


def test_split_temporal_no_mezcla_fechas(ventas):
    df = construir_dataset_diario(ventas)
    df = agregar_targets(df, HORIZONTES)
    train, test, corte = split_temporal(df, target_col="target_h1")
    assert train["fecha"].max() <= corte
    assert test["fecha"].min() > corte
    assert len(train) > 0 and len(test) > 0


def test_calidad_datos_marca_historico_insuficiente(ventas):
    df = construir_dataset_diario(ventas)
    resumen = calidad_datos_por_producto(df, minimo=1000)
    assert not resumen["calidad_suficiente"].any()

    resumen_bajo = calidad_datos_por_producto(df, minimo=1)
    assert resumen_bajo["calidad_suficiente"].all()
