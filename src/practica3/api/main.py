"""API FastAPI de predicción de demanda (Práctica 3).

Capa delgada sobre `practica3.inference.DemandPredictor` — sin lógica de negocio
propia. Endpoints documentados en `docs/04_api_reference.md`.

Arranque: `make api` o `uv run uvicorn practica3.api.main:app --reload`.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from ..inference import DemandPredictor
from ..training import ReentrenamientoError, reentrenar_con_csv
from .schemas import (
    AlertaRequest,
    AlertaResponse,
    BatchPredictRequest,
    BatchPredictResponse,
    BusinessMetricsResponse,
    ExplainRequest,
    ExplainResponse,
    HealthResponse,
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
    ReentrenarResponse,
    ReporteDemandaResponse,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("practica3.api")

_state: dict[str, DemandPredictor | None] = {"predictor": None}

_SEPARADOR = "=" * 78


def _nuevo_lote_id() -> str:
    return f"LOTE-{secrets.token_hex(4).upper()}"


def _log_paso(lote_id: str, paso: int, total_pasos: int, evento: str, mensaje: str, data: dict) -> None:
    """Log narrado paso a paso (mensaje en criollo + evento + payload JSON completo)
    para poder seguir en vivo qué está haciendo el backend con cada request."""
    texto = f"{lote_id} | PASO {paso}/{total_pasos} | {mensaje}"
    payload = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "level": "info",
        "event": evento,
        "message": texto,
        "data": {"lote_id": lote_id, "paso": paso, "total_pasos": total_pasos, **data},
    }
    logger.info(
        "\n%s\nMENSAJE: %s\nEVENTO: %s\nJSON:\n%s\n%s",
        _SEPARADOR,
        texto,
        evento,
        json.dumps(payload, indent=2, ensure_ascii=False),
        _SEPARADOR,
    )


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_methods=["*"],
    allow_headers=["*"],
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
    lote_id = _nuevo_lote_id()
    total_pasos = 4
    fechas = sorted({item.fecha for item in req.items})

    _log_paso(
        lote_id,
        1,
        total_pasos,
        "prediction.batch_received",
        f"Solicitud recibida para calcular {len(req.items)} producto(s) hasta el {fechas[-1]}.",
        {"productos_solicitados": len(req.items), "fechas_pedidas": fechas},
    )

    predictor = _predictor()
    _log_paso(
        lote_id,
        2,
        total_pasos,
        "prediction.batch_model_ready",
        "Los modelos SVR (por horizonte) ya están cargados en memoria y listos para procesar el lote.",
        {"horizontes_soportados": predictor.info_modelo()["horizontes_soportados"]},
    )

    resultados = []
    for item in req.items:
        try:
            resultados.append(predictor.predecir(item.product_id, item.fecha, item.horizonte))
        except ValueError as exc:
            _log_paso(
                lote_id,
                3,
                total_pasos,
                "prediction.batch_item_error",
                f"Falló el producto {item.product_id}: {exc}",
                {"product_id": item.product_id, "fecha": item.fecha, "horizonte": item.horizonte},
            )
            raise HTTPException(status_code=400, detail=f"product_id={item.product_id}: {exc}") from exc

    _log_paso(
        lote_id,
        3,
        total_pasos,
        "prediction.batch_computed",
        f"Se calcularon las {len(resultados)} predicciones pedidas sin errores.",
        {"product_ids": [r["product_id"] for r in resultados]},
    )

    top = max(resultados, key=lambda r: r["prediccion_esperada"]) if resultados else None
    _log_paso(
        lote_id,
        4,
        total_pasos,
        "prediction.batch_done",
        (
            f"Lote resuelto. Mayor demanda esperada: producto {top['product_id']} con "
            f"{top['prediccion_esperada']:.1f} u."
            if top
            else "Lote resuelto sin resultados."
        ),
        {"top_product_id": top["product_id"] if top else None},
    )

    return BatchPredictResponse(resultados=resultados)


@app.post("/predict/alerta", response_model=AlertaResponse)
def predict_alerta(req: AlertaRequest) -> AlertaResponse:
    try:
        resultado = _predictor().predecir_alerta(req.product_id, req.fecha)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AlertaResponse(**resultado)


@app.get("/metrics/negocio", response_model=BusinessMetricsResponse)
def metrics_negocio() -> BusinessMetricsResponse:
    return BusinessMetricsResponse(**_predictor().metricas_negocio())


@app.post("/predict/explain", response_model=ExplainResponse)
def predict_explain(req: ExplainRequest) -> ExplainResponse:
    try:
        resultado = _predictor().explicar(req.product_id, req.fecha, req.horizonte)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ExplainResponse(**resultado)


@app.get("/reportes/demanda-periodo", response_model=ReporteDemandaResponse)
def reporte_demanda_periodo(fecha: str) -> ReporteDemandaResponse:
    try:
        resultado = _predictor().reporte_demanda(fecha)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReporteDemandaResponse(**resultado)


def _exigir_admin(token: str | None) -> None:
    """El reentrenamiento reescribe ventas.csv y los modelos: solo con clave.

    Sin `PRACTICA3_ADMIN_TOKEN` definido el endpoint queda apagado.
    """
    esperado = os.environ.get("PRACTICA3_ADMIN_TOKEN")
    if not esperado:
        raise HTTPException(
            status_code=403,
            detail="Reentrenamiento deshabilitado: definir PRACTICA3_ADMIN_TOKEN al arrancar la API.",
        )
    if not token or not secrets.compare_digest(token, esperado):
        raise HTTPException(status_code=401, detail="Clave de administrador incorrecta.")


@app.post("/admin/reentrenar", response_model=ReentrenarResponse)
async def reentrenar(
    file: UploadFile = File(...),
    x_admin_token: str | None = Header(default=None),
) -> ReentrenarResponse:
    """Sube ventas nuevas (mismo esquema de `ventas.csv`) y reentrena los modelos.

    Reutiliza los hiperparámetros ya encontrados por GridSearchCV en el notebook 2
    (no repite la búsqueda) — reentrenamiento rápido, pensado para correr on-demand
    desde la beta, no una re-ejecución completa del pipeline de investigación.
    """
    _exigir_admin(x_admin_token)
    contenido = await file.read()
    try:
        resumen = reentrenar_con_csv(contenido)
    except ReentrenamientoError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _state["predictor"] = DemandPredictor()
    logger.info("Modelos reentrenados y recargados (%s filas nuevas)", resumen["filas_nuevas_agregadas"])
    return ReentrenarResponse(**resumen)
