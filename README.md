# Práctica 3 — Predicción de demanda (SVR multi-horizonte)

**Aprendizaje Automático · Michael Franco, Michael Lata, Jordy Romero, Nayeli Barbecho**

Continúa la línea Práctica 2 (LSTM/boosting, sintético) → Informe SVM (SVR simple,
sintético) → esta práctica: mismo enfoque SVR, "producción-lista" (API + docs +
tests), corriendo ahora sobre **ventas reales de El Café que te Conté**
(2026-04-01 a 2026-07-31, 33 productos), con las mejoras concretas pedidas por las
empresas en `Material y Reportes/Feedback Empresas.pdf` §V (horizontes múltiples,
intervalos, alertas, anomalías, métricas de negocio, reporte no técnico).

## Resultados (horizonte t+1, test, datos reales)

| Métrica | Valor |
|---|---|
| RMSE | 10.94 |
| MAE | 7.75 |
| R² | **0.46** |
| Reducción de ingresos en riesgo vs baseline ingenuo (`lag_7`) | **32%** |

De 24 features candidatas (calendario + 3 variables reales nuevas: precio,
tráfico de clientes, hora de venta), la selección por `permutation importance`
dejó 9 para el SVR. El SVC de alerta y el `IsolationForest` usan las 24
candidatas completas — se detectó y corrigió un error metodológico real: reusar
las features podadas para el SVR en el SVC bajaba su AUC a 0.47 (peor que azar);
con las 24 candidatas sube a 0.60 (detalle en `docs/01_arquitectura.md`).

Las métricas de la etapa sintética (Práctica 2, Informe SVM) quedan en
`models/metadata.json` solo como contexto histórico — **no son comparables
numéricamente** (dataset, escala y productos distintos).

## Estructura

```
docs/           arquitectura, glosario, runbook, api reference
notebooks/      01_data · 02_procesos · 03_resultados
src/practica3/  features.py + inference.py (compartidos por notebooks y API)
data/raw/       ventas.csv (export real, nivel ticket/línea)
models/         artefactos entrenados (generados por 02_procesos)
metrics/        metrics.json (generado por 03_resultados)
reports/        reporte_ejecutivo.md (generado por 03_resultados)
jmeter/         plan_practica3.jmx
```

## Quickstart

```bash
sudo pacman -S uv          # o: curl -LsSf https://astral.sh/uv/install.sh | sh
make setup                 # uv sync + kernel de Jupyter + nbstripout
make pipeline               # 01_data -> 02_procesos -> 03_resultados
make api                    # http://localhost:8000/docs
make test
```

Detalle completo de instalación y solución de problemas en `docs/03_runbook.md`.

## Documentación

- [`docs/01_arquitectura.md`](docs/01_arquitectura.md) — flujo de datos y componentes
- [`docs/02_glosario.md`](docs/02_glosario.md) — términos y decisiones de arquitectura
- [`docs/03_runbook.md`](docs/03_runbook.md) — setup, troubleshooting y cómo actualizar con un nuevo export de ventas
- [`docs/04_api_reference.md`](docs/04_api_reference.md) — endpoints de la API

## Qué mejora esta práctica, concretamente

Cada punto de `Feedback Empresas.pdf` §V tiene una implementación 1:1: horizontes
múltiples (`svr_h1/h3/h7`), intervalos de confianza (cuantiles empíricos de
residuos), importancia de variables (`permutation_importance`), detección de
anomalías (`IsolationForest`), métricas de negocio con **precio real** (ingresos en
riesgo por quiebre/sobre-stock, sin márgenes inventados), reporte automático no
técnico (`reports/reporte_ejecutivo.md`) e indicador de riesgo fácil de leer
(semáforo verde/amarillo/rojo). Detalle en `docs/01_arquitectura.md` y
`docs/02_glosario.md`.

## De datos sintéticos a datos reales

Esta práctica arrancó sobre el dataset sintético de la Práctica 2. Con el export
real de El Café que te Conté (`data/raw/ventas.csv`), se retiraron 3 variables
sintéticas sin respaldo (`proporcion_stock`, `promocion_activa`, `clima_lluvia`) y
se agregaron 3 reales (`precio_promedio`, `n_tickets_dia`, `hora_promedio_venta`) —
sin cambiar la arquitectura del pipeline.

## Pendiente

- Correr `make loadtest` (JMeter) contra la API — instalación en `docs/03_runbook.md`.
- Cuando la cafetería acumule más meses de ventas, actualizar `ventas.csv` y
  volver a correr `make pipeline` (ver `docs/03_runbook.md`).
