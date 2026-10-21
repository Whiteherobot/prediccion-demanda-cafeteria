# API Reference

FastAPI, `src/practica3/api/main.py`. Arranque: `make api` → `http://localhost:8000`
(documentación interactiva autogenerada en `/docs`). Todos los endpoints de
predicción devuelven `503` si `models/` todavía no existe (correr `make train`).

Datos: ventas reales de **El Café que te Conté**, 2026-04-01 a 2026-07-31, 33
productos (`product_id` 1-33, asignado por orden alfabético del nombre real —
consultar `GET /model/info` o `data/processed/data_quality_report.json` para el
mapeo). Las fechas de ejemplo de este documento están dentro de ese rango.

## `GET /health`

Liveness check, no requiere modelos cargados.

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok"}
```

## `GET /model/info`

Features usadas por cada modelo, horizontes soportados, métricas del modelo activo
y calidad de datos histórica por producto. El SVR y el SVC/IsolationForest usan
**conjuntos de features distintos** (ver `docs/01_arquitectura.md`).

```bash
curl http://localhost:8000/model/info
```

```json
{
  "features_svr": ["cantidad_vendida", "dias_desde_inicio", "categoria_encoded",
                    "rolling_mean_7", "rolling_std_7", "rolling_mean_14",
                    "dia_semana_sin", "dia_semana_cos", "precio_promedio"],
  "features_svc_iso": ["cantidad_vendida", "dia_semana", "mes", "...", "n_tickets_dia"],
  "horizontes_soportados": [1, 3, 7],
  "metricas": {"1": {"rmse": 11.27, "mae": 7.99, "r2": 0.43}, "3": {...}, "7": {...}},
  "calidad_datos_por_producto": {"1": true, "2": true, "...": "..."}
}
```

## `POST /predict`

Predicción de demanda para un producto, con escenarios e indicador de riesgo.
`fecha` es la **fecha de referencia** (hasta donde hay datos conocidos); la API
calcula sola `fecha_objetivo = fecha_referencia_datos + horizonte`.

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"product_id": 5, "fecha": "2026-07-15", "horizonte": 1}'
```

**Request**

| Campo | Tipo | Descripción |
|---|---|---|
| `product_id` | int | Identificador del producto (1-33) |
| `fecha` | string | Fecha de referencia `YYYY-MM-DD` (dentro del histórico: 2026-04-01 a 2026-07-31) |
| `horizonte` | int | `1`, `3` o `7` días adelante (default `1`) |

**Response**

```json
{
  "product_id": 5,
  "fecha_solicitada": "2026-07-15",
  "fecha_referencia_datos": "2026-07-15",
  "fecha_objetivo": "2026-07-16",
  "horizonte_dias": 1,
  "prediccion_esperada": 13.12,
  "escenario_conservador": 4.03,
  "escenario_optimista": 27.84,
  "nivel_riesgo": "amarillo",
  "alerta_alta_demanda": false,
  "alerta_anomalia": false,
  "datos_historicos_suficientes": true
}
```

`400` si el horizonte no está soportado o si no hay histórico para ese producto en
o antes de la fecha pedida.

## `POST /predict/batch`

Mismo request/response que `/predict`, en lote.

```bash
curl -X POST http://localhost:8000/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"items": [
        {"product_id": 5, "fecha": "2026-07-15", "horizonte": 1},
        {"product_id": 7, "fecha": "2026-07-15", "horizonte": 7}
      ]}'
```

```json
{"resultados": [{"product_id": 5, "...": "..."}, {"product_id": 7, "...": "..."}]}
```

## `POST /predict/alerta`

Clasificación SVC standalone de "día de alta demanda" (horizonte fijo t+1), con la
probabilidad del clasificador.

```bash
curl -X POST http://localhost:8000/predict/alerta \
  -H "Content-Type: application/json" \
  -d '{"product_id": 5, "fecha": "2026-07-15"}'
```

```json
{
  "product_id": 5,
  "fecha_solicitada": "2026-07-15",
  "fecha_referencia_datos": "2026-07-15",
  "alerta_alta_demanda": false,
  "probabilidad": 0.0589
}
```

## Códigos de estado

| Código | Cuándo |
|---|---|
| `200` | OK |
| `400` | Horizonte no soportado o sin histórico suficiente para la fecha/producto pedidos |
| `422` | Payload inválido (validación de Pydantic — tipos, campos faltantes) |
| `503` | Modelos no entrenados todavía (`models/` vacío) |
