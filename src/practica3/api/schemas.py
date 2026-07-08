"""Modelos Pydantic de request/response de la API. Ver docs/04_api_reference.md."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"


class ModelInfoResponse(BaseModel):
    features_svr: list[str]
    features_svc_iso: list[str]
    horizontes_soportados: list[int]
    metricas: dict
    calidad_datos_por_producto: dict[int, bool]


class PredictRequest(BaseModel):
    product_id: int = Field(..., ge=1, description="Identificador del producto (1-33)")
    fecha: str = Field(..., description="Fecha de referencia YYYY-MM-DD (datos conocidos hasta ese día)")
    horizonte: int = Field(1, description="Días hacia adelante a predecir: 1, 3 o 7")


class PredictResponse(BaseModel):
    product_id: int
    fecha_solicitada: str
    fecha_referencia_datos: str
    fecha_objetivo: str
    horizonte_dias: int
    prediccion_esperada: float
    escenario_conservador: float
    escenario_optimista: float
    nivel_riesgo: str
    alerta_alta_demanda: bool
    alerta_anomalia: bool
    datos_historicos_suficientes: bool


class BatchPredictRequest(BaseModel):
    items: list[PredictRequest]


class BatchPredictResponse(BaseModel):
    resultados: list[PredictResponse]


class AlertaRequest(BaseModel):
    product_id: int = Field(..., ge=1)
    fecha: str = Field(..., description="Fecha de referencia YYYY-MM-DD")


class AlertaResponse(BaseModel):
    product_id: int
    fecha_solicitada: str
    fecha_referencia_datos: str
    alerta_alta_demanda: bool
    probabilidad: float


class ErrorResponse(BaseModel):
    detail: str
