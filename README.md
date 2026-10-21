# Predicción de demanda para una cafetería

[![CI](https://github.com/Whiteherobot/prediccion-demanda-cafeteria/actions/workflows/ci.yml/badge.svg)](https://github.com/Whiteherobot/prediccion-demanda-cafeteria/actions/workflows/ci.yml)

Predice cuántas unidades de cada producto va a vender **El Café que te Conté** (Cuenca) a 1, 3
y 7 días, con un rango de escenarios, una alerta de día de alta demanda y un aviso cuando el
contexto se sale de lo normal. Se entrena con el export real del POS (ticket por línea, del
1 de abril al 31 de julio de 2026, 33 productos) y se sirve con una API FastAPI y una beta en
Angular.

Práctica 3 de Aprendizaje Automático (UPS, 2026), hecha por Michael Lata, Michael Franco,
Jordy Romero y Nayeli Barbecho.

## Resultados (test, últimos días del rango)

| Horizonte | RMSE | MAE | R² |
|---|---|---|---|
| t+1 | 11.27 | 7.99 | 0.43 |
| t+3 | 11.12 | 7.90 | 0.45 |
| t+7 | 11.03 | 7.67 | 0.45 |

Contra el baseline ingenuo (vender lo mismo que hace una semana), el modelo reduce un **30 %**
el dinero en riesgo por quiebre o sobrante, calculado con el precio real de cada producto.

- **Modelo:** un SVR (kernel RBF) por horizonte. De 24 variables candidatas (calendario,
  historia de ventas, precio, tickets del día y hora típica de venta), `permutation_importance`
  deja 10.
- **Alerta de alta demanda:** un SVC con las 24 candidatas (AUC 0.62). Con las 10 del SVR
  baja a 0.57: la selección hecha para regresión no sirve para clasificar.
- **Anomalías:** `IsolationForest`. **Escenarios:** cuantiles empíricos de los residuos.
- **Explicación:** Kernel SHAP por predicción (notebook 3 y `POST /predict/explain`).

## Uso

```bash
make setup        # uv sync + nbstripout
make pipeline     # 01_data -> 02_procesos -> 03_resultados (unos 2 minutos)
make test
make api          # http://localhost:8000/docs
```

La beta (`beta_prediccion_demanda/`) corre con `npm ci && npm start` en
http://localhost:4200, con la API levantada. La carga de ventas nuevas reentrena los modelos y
reescribe `data/raw/ventas.csv`, así que solo funciona si la API se arranca con una clave:

```bash
PRACTICA3_ADMIN_TOKEN=una-clave-larga make api
```

Detalle de instalación, actualización con un export nuevo y problemas comunes en
[`docs/03_runbook.md`](docs/03_runbook.md). Video de la beta (1 min):
[Drive](https://drive.google.com/file/d/1Czsoc6Qy0FZf6Afn7Mvh4-pwxvy2_ocg/view?usp=sharing).

## Estructura

```
src/practica3/   features.py e inference.py (los usan los notebooks y la API), training.py, api/
notebooks/       01_data, 02_procesos, 03_resultados (se entregan ejecutados)
data/raw/        ventas.csv
docs/            arquitectura, glosario, runbook, referencia de la API
reports/         reporte ejecutivo para la cafetería (lo genera el notebook 3)
beta_prediccion_demanda/   front en Angular + PrimeNG
jmeter/          plan de carga de la API
```

## Historia

- **Práctica 2:** LSTM y boosting sobre un dataset sintético.
- **Informe SVM:** el mismo problema con un SVR simple, todavía sintético.
- **Práctica 3 (julio 2026):** SVR multi-horizonte, API y documentación. A mitad de la práctica
  la cafetería entregó sus ventas reales: se quitaron las variables inventadas (stock, promoción,
  lluvia) y entraron las reales (precio, tickets del día, hora de venta). Las mejoras (escenarios,
  alertas, anomalías, métricas en dólares y reporte no técnico) salen de la retroalimentación
  que dio la cafetería.
- **Revisión de octubre 2026:**
  - El export solo trae los días con venta, así que los lags y los objetivos se corrían por
    filas en lugar de por días. Ahora hay una grilla de calendario completa y un día sin venta
    cuenta como 0; el R² t+1 pasó de 0.46 a 0.43.
  - El reentrenamiento escribía `ventas.csv` antes de validar el CSV. Ahora valida todo
    primero, escribe de forma atómica y pide una clave.
  - Se agregaron CI y la licencia, y se sacaron del repo los zips de entrega.

## Licencia

MIT. Ver [LICENSE](LICENSE).
