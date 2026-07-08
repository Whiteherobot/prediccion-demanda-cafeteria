# API Reference

FastAPI, `src/practica3/api/main.py`. Arranque: `make api` → `http://localhost:8000`
(documentación interactiva autogenerada en `/docs`). Todos los endpoints de
predicción devuelven `503` si `models/` todavía no existe (correr `make train`).

## `GET /health`

Liveness check, no requiere modelos cargados.

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok"}
```

## `GET /model/info`

Features usadas, horizontes soportados, métricas del modelo activo y calidad de
datos histórica por producto.

```bash
curl http://localhost:8000/model/info
```

```json
{
  "features": ["cantidad_vendida", "dia_semana", "...", "flujo_clientes_estimado"],
  "horizontes_soportados": [1, 3, 7],
  "metricas": {"1": {"rmse": 4.8, "mae": 3.6, "r2": 0.46}, "3": {...}, "7": {...}},
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
  -d '{"product_id": 1, "fecha": "2026-09-25", "horizonte": 1}'
```

**Request**

| Campo | Tipo | Descripción |
|---|---|---|
| `product_id` | int | Identificador del producto (1-10 en el dataset sintético) |
| `fecha` | string | Fecha de referencia `YYYY-MM-DD` |
| `horizonte` | int | `1`, `3` o `7` días adelante (default `1`) |

**Response**

```json
{
  "product_id": 1,
  "fecha_solicitada": "2026-09-25",
  "fecha_referencia_datos": "2026-09-25",
  "fecha_objetivo": "2026-09-26",
  "horizonte_dias": 1,
  "prediccion_esperada": 9.4,
  "escenario_conservador": 6.1,
  "escenario_optimista": 13.2,
  "nivel_riesgo": "verde",
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
        {"product_id": 1, "fecha": "2026-09-25", "horizonte": 1},
        {"product_id": 2, "fecha": "2026-09-25", "horizonte": 7}
      ]}'
```

```json
{"resultados": [{"product_id": 1, "...": "..."}, {"product_id": 2, "...": "..."}]}
```

## `POST /predict/alerta`

Clasificación SVC standalone de "día de alta demanda" (horizonte fijo t+1), con la
probabilidad del clasificador.

```bash
curl -X POST http://localhost:8000/predict/alerta \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "fecha": "2026-09-25"}'
```

```json
{
  "product_id": 1,
  "fecha_solicitada": "2026-09-25",
  "fecha_referencia_datos": "2026-09-25",
  "alerta_alta_demanda": true,
  "probabilidad": 0.83
}
```

## Códigos de estado

| Código | Cuándo |
|---|---|
| `200` | OK |
| `400` | Horizonte no soportado o sin histórico suficiente para la fecha/producto pedidos |
| `422` | Payload inválido (validación de Pydantic — tipos, campos faltantes) |
| `503` | Modelos no entrenados todavía (`models/` vacío) |
