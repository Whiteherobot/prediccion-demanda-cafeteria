"""Reentrenamiento sobre una copia de data/ y models/ en un directorio temporal:
nunca toca el histórico real."""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

from practica3 import training

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    not (ROOT / "models" / "metadata.json").exists(),
    reason="Faltan artefactos en models/ — correr `make train` o `make pipeline` primero",
)


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    for sub in ("data/raw", "models", "metrics"):
        (tmp_path / sub).mkdir(parents=True)
    shutil.copy(ROOT / "data/raw/ventas.csv", tmp_path / "data/raw/ventas.csv")
    for f in (ROOT / "models").glob("*"):
        if f.suffix in {".joblib", ".json"}:
            shutil.copy(f, tmp_path / "models" / f.name)
    shutil.copy(ROOT / "metrics/metrics.json", tmp_path / "metrics/metrics.json")

    monkeypatch.setattr(training, "DATA_RAW_DIR", tmp_path / "data/raw")
    monkeypatch.setattr(training, "VENTAS_PATH", tmp_path / "data/raw/ventas.csv")
    monkeypatch.setattr(training, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(training, "METRICS_PATH", tmp_path / "metrics/metrics.json")
    return tmp_path


def _dia_siguiente() -> pd.DataFrame:
    """Repite las ventas del último día un día después, con tickets nuevos."""
    ventas = pd.read_csv(ROOT / "data/raw/ventas.csv")
    fechas = pd.to_datetime(ventas["fecha_completa"], format="%d/%m/%Y")
    ultimo = ventas[fechas == fechas.max()].copy()
    nueva = fechas.max() + pd.Timedelta(days=1)
    ultimo["fecha_completa"] = nueva.strftime("%d/%m/%Y")
    ultimo["id_ticket"] = "NUEVO_" + ultimo["id_ticket"].astype(str)
    return ultimo


def test_csv_con_fecha_invalida_no_toca_el_historico(entorno):
    antes = (entorno / "data/raw/ventas.csv").read_bytes()
    malo = _dia_siguiente()
    malo.iloc[3, malo.columns.get_loc("fecha_completa")] = "2026-08-01"

    with pytest.raises(training.ReentrenamientoError, match="fecha_completa.*filas \\[5\\]"):
        training.reentrenar_con_csv(malo.to_csv(index=False).encode())

    assert (entorno / "data/raw/ventas.csv").read_bytes() == antes
    assert not list((entorno / "data/raw").glob("ventas_backup_*"))


def test_csv_repetido_no_aporta_filas(entorno):
    ya_existentes = pd.read_csv(ROOT / "data/raw/ventas.csv").tail(50)
    with pytest.raises(training.ReentrenamientoError, match="no aportó filas nuevas"):
        training.reentrenar_con_csv(ya_existentes.to_csv(index=False).encode())


def test_reentrena_agrega_filas_y_deja_respaldo(entorno):
    nuevas = _dia_siguiente()
    resumen = training.reentrenar_con_csv(nuevas.to_csv(index=False).encode())

    assert resumen["filas_nuevas_agregadas"] == len(nuevas)
    assert resumen["rango_fechas"].endswith("2026-08-01")
    assert (entorno / "data/raw" / resumen["backup_creado"]).exists()
    assert set(resumen["metricas"]) == {"1", "3", "7"}
    assert not list(entorno.rglob("*.tmp"))
