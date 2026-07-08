"""API FastAPI de predicción de demanda (Práctica 3).

Capa delgada sobre `practica3.inference.DemandPredictor` — sin lógica de negocio
propia. Endpoints documentados en `docs/04_api_reference.md`.

Arranque: `make api` o `uv run uvicorn practica3.api.main:app --reload`.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from ..inference import DemandPredictor
from .schemas import (
    AlertaRequest,
    AlertaResponse,
    BatchPredictRequest,
    BatchPredictResponse,
    HealthResponse,
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
)

logger = logging.getLogger("practica3.api")

_state: dict[str, DemandPredictor | None] = {"predictor": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        _state["predictor"] = DemandPredictor()
        logger.info("Modelos cargados desde models/")
    except FileNotFoundError as exc:
        logger.warning("No se pudieron cargar los modelos (%s). Correr `make train` primero.", exc)
        _state["predictor"] = None
    yield
    _state.clear()


app = FastAPI(
    title="Práctica 3 — API de predicción de demanda",
    description="SVR multi-horizonte con escenarios, alerta de alta demanda y detección de anomalías.",
    version="1.0.0",
    lifespan=lifespan,
)


def _predictor() -> DemandPredictor:
    predictor = _state["predictor"]
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modelo no entrenado todavía. Correr `make train` (o `make pipeline`) y reiniciar la API.",
        )
    return predictor


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/model/info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    return ModelInfoResponse(**_predictor().info_modelo())


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest) -> PredictResponse:
    try:
        resultado = _predictor().predecir(req.product_id, req.fecha, req.horizonte)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PredictResponse(**resultado)


@app.post("/predict/batch", response_model=BatchPredictResponse)
def predict_batch(req: BatchPredictRequest) -> BatchPredictResponse:
    predictor = _predictor()
    resultados = []
    for item in req.items:
        try:
            resultados.append(predictor.predecir(item.product_id, item.fecha, item.horizonte))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"product_id={item.product_id}: {exc}") from exc
    return BatchPredictResponse(resultados=resultados)


@app.post("/predict/alerta", response_model=AlertaResponse)
def predict_alerta(req: AlertaRequest) -> AlertaResponse:
    try:
        resultado = _predictor().predecir_alerta(req.product_id, req.fecha)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AlertaResponse(**resultado)
