# Práctica 3 — Predicción de demanda (SVR multi-horizonte)

**Aprendizaje Automático · Michael Franco, Michael Lata, Jordy Romero, Nayeli Barbecho**

Continúa la línea Práctica 2 (LSTM/boosting) → Informe SVM (SVR simple, R²≈0.42) →
esta práctica: mismo SVR, "producción-lista" (API + docs + CI-ready) y con las
mejoras concretas pedidas por las empresas en `Material y Reportes/Feedback
Empresas.pdf` §V (horizontes múltiples, intervalos, alertas, anomalías, métricas de
negocio, reporte no técnico). Datos sintéticos de la Práctica 2, reutilizados sin
cambios, mientras llega el Excel real de El Café que te Conté.

## Resultados (horizonte t+1, test)

| Modelo | RMSE | MAE | R² |
|---|---|---|---|
| Práctica 2 (LSTM/boosting) | 7.12 | 5.21 | 0.28 |
| Informe SVM (12 features) | 5.11 | 3.65 | 0.42 |
| **Práctica 3 (18 features, seleccionadas de 25 candidatas)** | **5.18** | **3.62** | **0.41** |

Rendimiento equivalente al Informe SVM (dentro del margen de ruido de ~290 filas de
test) **más**: predicción a `t+3`/`t+7`, intervalos de escenarios, alerta de alta
demanda, detección de anomalías y ≈44% menos costo estimado que un baseline ingenuo
(`métricas de negocio`, ver `metrics/metrics.json`). De 25 features candidatas
(12 originales + 13 nuevas), la selección por `permutation importance` descartó 7
sin señal real — la mayoría, variables exógenas sintéticas que se recalcularán con
datos reales.

## Estructura

```
docs/           arquitectura, glosario, runbook, api reference
notebooks/      01_data · 02_procesos · 03_resultados
src/practica3/  features.py + inference.py (compartidos por notebooks y API)
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
- [`docs/03_runbook.md`](docs/03_runbook.md) — setup y troubleshooting
- [`docs/04_api_reference.md`](docs/04_api_reference.md) — endpoints de la API

## Qué mejora esta práctica, concretamente

Cada punto de `Feedback Empresas.pdf` §V tiene una implementación 1:1: horizontes
múltiples (`svr_h1/h3/h7`), intervalos de confianza (cuantiles empíricos de
residuos), importancia de variables (`permutation_importance`), detección de
anomalías (`IsolationForest`), métricas de negocio (costo de quiebre/sobre-stock),
reporte automático no técnico (`reports/reporte_ejecutivo.md`) e indicador de
riesgo fácil de leer (semáforo verde/amarillo/rojo). Detalle en
`docs/01_arquitectura.md` y `docs/02_glosario.md`.

## Pendiente

- Reemplazar variables sintéticas (`promocion_activa`, `clima_lluvia`, etc.) por
  datos reales cuando llegue el Excel de la empresa.
- Correr `make loadtest` (JMeter) contra la API — instalación en `docs/03_runbook.md`.
