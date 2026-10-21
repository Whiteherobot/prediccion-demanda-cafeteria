"""Tests de la API. Los endpoints de predicción requieren `make train` ejecutado antes
(necesitan los artefactos en models/); si no existen, esos tests se saltan mostrando
el motivo en vez de fallar en un entorno recién clonado."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from practica3.api.main import app

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
modelos_disponibles = (MODELS_DIR / "metadata.json").exists()

requiere_modelos = pytest.mark.skipif(
    not modelos_disponibles,
    reason="Faltan artefactos en models/ — correr `make train` o `make pipeline` primero",
)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_no_requiere_modelo(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@requiere_modelos
def test_model_info(client):
    r = client.get("/model/info")
    assert r.status_code == 200
    body = r.json()
    assert "features_svr" in body and len(body["features_svr"]) > 0
    assert "features_svc_iso" in body and len(body["features_svc_iso"]) > 0
    assert set(body["horizontes_soportados"]) == {1, 3, 7}


@requiere_modelos
def test_predict_producto_valido(client):
    r = client.post("/predict", json={"product_id": 1, "fecha": "2026-07-15", "horizonte": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["product_id"] == 1
    assert (
        body["escenario_conservador"] <= body["prediccion_esperada"] <= body["escenario_optimista"]
    )
    assert body["nivel_riesgo"] in {"verde", "amarillo", "rojo"}


@requiere_modelos
def test_predict_horizonte_invalido(client):
    r = client.post("/predict", json={"product_id": 1, "fecha": "2026-07-15", "horizonte": 2})
    assert r.status_code == 400


@requiere_modelos
def test_predict_batch(client):
    r = client.post(
        "/predict/batch",
        json={
            "items": [
                {"product_id": 1, "fecha": "2026-07-15", "horizonte": 1},
                {"product_id": 2, "fecha": "2026-07-15", "horizonte": 3},
            ]
        },
    )
    assert r.status_code == 200
    assert len(r.json()["resultados"]) == 2


@requiere_modelos
def test_predict_alerta(client):
    r = client.post("/predict/alerta", json={"product_id": 1, "fecha": "2026-07-15"})
    assert r.status_code == 200
    body = r.json()
    assert 0.0 <= body["probabilidad"] <= 1.0


def test_reentrenar_apagado_sin_clave_configurada(client, monkeypatch):
    monkeypatch.delenv("PRACTICA3_ADMIN_TOKEN", raising=False)
    r = client.post("/admin/reentrenar", files={"file": ("v.csv", b"a,b\n1,2\n")})
    assert r.status_code == 403


def test_reentrenar_rechaza_clave_incorrecta(client, monkeypatch):
    monkeypatch.setenv("PRACTICA3_ADMIN_TOKEN", "correcta")
    archivo = {"file": ("v.csv", b"a,b\n1,2\n")}
    assert client.post("/admin/reentrenar", files=archivo).status_code == 401
    r = client.post("/admin/reentrenar", files=archivo, headers={"X-Admin-Token": "otra"})
    assert r.status_code == 401
    # Con la clave correcta pasa al validador del CSV (que rechaza este esquema).
    r = client.post("/admin/reentrenar", files=archivo, headers={"X-Admin-Token": "correcta"})
    assert r.status_code == 400
