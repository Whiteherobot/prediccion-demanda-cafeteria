# Arquitectura

## Flujo de datos y componentes

```
data/raw/ventas.csv (export real, El Café que te Conté, nivel ticket/línea)
        │
        ▼
notebooks/01_data.ipynb ──uses──▶ src/practica3/features.py
        │  (EDA, 24 features candidatas, calidad de datos, targets multi-horizonte)
        ▼
data/processed/{dataset_features.parquet, features.json, data_quality_report.json}
        │
        ▼
notebooks/02_procesos.ipynb ──uses──▶ src/practica3/features.py
        │  (selección de features, SVR x3 horizontes, SVC alerta, IsolationForest,
        │   intervalos, importancia)
        ▼
models/{svr_h1,h3,h7.joblib, svc_alerta.joblib, isolation_forest.joblib,
        residuales.json, metadata.json}
        │
        ├──▶ notebooks/03_resultados.ipynb ──▶ metrics/metrics.json
        │                                   └─▶ reports/reporte_ejecutivo.md
        │
        └──▶ src/practica3/inference.py (DemandPredictor)
                    │
                    ▼
             src/practica3/api/main.py (FastAPI)
                    │
                    ▼
             jmeter/plan_practica3.jmx (emula usuarios contra la API)
```

`src/practica3/features.py` es el único lugar donde vive la ingeniería de
features. Los notebooks y la API lo importan — no hay lógica duplicada entre el
entrenamiento y el servicio, que es la causa más común de *training/serving skew*
en un sistema de ML real.

## Componentes

| Componente | Responsabilidad |
|---|---|
| `src/practica3/features.py` | Carga `ventas.csv`, construye el dataset diario (24 features candidatas) y el split temporal. Sin estado, sin I/O de red. |
| `src/practica3/inference.py` | Carga los artefactos de `models/` y expone `DemandPredictor.predecir()`: punto estimado, escenarios, riesgo, alertas. |
| `src/practica3/api/` | FastAPI: expone `inference.py` por HTTP. Sin lógica de negocio propia — es una capa delgada. |
| `notebooks/01_data.ipynb` | Datos: carga, EDA, features, calidad de datos, targets. |
| `notebooks/02_procesos.ipynb` | Entrenamiento: selección de features, SVR multi-horizonte, SVC, anomalías, intervalos. |
| `notebooks/03_resultados.ipynb` | Resultados: métricas técnicas y de negocio (con precio real), gráficos, XAI (SHAP) y reportes. |
| `jmeter/plan_practica3.jmx` | Simula usuarios concurrentes contra `/health` y `/predict`. |

## De datos sintéticos a datos reales

Esta práctica arrancó sobre el dataset sintético de la Práctica 2 (10 productos
electrónicos, generado por código) y el SVR del Informe SVM. Cuando El Café que te
Conté entregó su export real de ventas (`ventas.csv`, 122 días, 33 productos, nivel
ticket/línea), el pipeline se adaptó **sin cambiar la arquitectura**: mismas
funciones (`construir_dataset_diario`, `split_temporal`), mismo flujo de
notebooks, misma API. Solo cambiaron las features disponibles:

- **Retiradas** (sin respaldo real): `proporcion_stock` (no hay inventario en el
  export), `promocion_activa`, `clima_lluvia` (no hay esas columnas).
- **Agregadas** (genuinamente reales, no estimadas): `precio_promedio` (precio real
  del producto ese día), `n_tickets_dia` (tráfico real de clientes, contado de
  tickets distintos), `hora_promedio_venta` (patrón horario real).

Las métricas de la etapa sintética (Práctica 2, Informe SVM) quedan citadas en
`models/metadata.json` solo como **contexto histórico** — no son comparables
numéricamente con los resultados sobre datos reales (productos, escala y ruido
distintos).

## Por qué SVR y no LSTM/boosting

La Práctica 2 entrenó LSTM + boosting sobre datos sintéticos. El Informe SVM mostró
que un SVR simple con `StandardScaler + GridSearchCV` iguala o supera a esos
modelos siendo determinista, sin GPU y mucho más liviano de mantener — justo lo que
necesita una empresa pequeña sin infraestructura de ML (ver `Feedback
Empresas.pdf`, donde dos de las tres empresas contactadas ni siquiera tienen
registros digitales). Sobre datos reales, esa misma arquitectura simple sigue
siendo la apuesta correcta: con 122 días de historia no hay margen para modelos
que necesiten mucho más volumen de datos.

## Por qué el SVR y el SVC/IsolationForest usan features distintas

La selección de features del notebook 2 (`permutation_importance`) se corre sobre
el **SVR** (predecir la cantidad exacta) y descarta las que no aportan ahí. Se
verificó empíricamente que reusar ese conjunto podado para el **SVC de alerta**
bajaba su AUC de 0.62 a 0.57 (con los datos sin grilla de calendario llegó a 0.47) — features irrelevantes para predecir una
cantidad pueden ser relevantes para clasificar "día alto vs normal". Por eso
`metadata.json` guarda dos listas (`feature_cols_svr` y `feature_cols_svc_iso`) y
`inference.py` construye un vector de entrada distinto para cada modelo.

## Por qué un dataset por horizonte en vez de un solo modelo recursivo

Predecir `t+3` o `t+7` encadenando 3-7 veces un modelo de `t+1` (forecast
recursivo) acumula error en cada paso. Entrenar un SVR independiente por horizonte
(mismo set de features, target distinto) es más simple, más rápido de auditar y
evita esa acumulación.

## XAI — por qué Kernel SHAP y no permutation importance a secas

La sección 7 del notebook 3 (`permutation_importance`) responde "¿qué variable
importa en promedio?" — es información **global**, no explica una predicción
puntual. La guía de práctica pide justificar predicciones individuales "hacia
atrás hasta la data original", así que el notebook agrega un proceso de **Kernel
SHAP** (`shap.KernelExplainer`) sobre el pipeline `StandardScaler + SVR`:

- Se eligió Kernel SHAP (no `LinearExplainer` ni `TreeExplainer`) porque el SVR
  con kernel RBF no es lineal ni basado en árboles — Kernel SHAP es
  model-agnostic, solo necesita `predict()`.
- El costo es cómputo: cada instancia explicada corre ~200 evaluaciones del
  modelo contra una muestra de referencia (`background`, 50 filas del train).
  Con 10 features y 4 instancias de ejemplo, toma segundos — no escalaría a
  explicar todo el dataset de test así, pero no hace falta para la guía.
- El proceso completo (6 pasos) queda documentado en la sección 8 del
  notebook, y aplicado a 2 pares de productos contrastantes (perecible/no
  perecible, popular fin de semana/canasta básica) en la sección 9, con
  trazabilidad hasta los tickets crudos de `ventas.csv`.

## Decisiones de infraestructura

- **`uv`** en vez de `pip`/`conda`: lockfile reproducible, instalación rápida,
  gestiona su propia versión de Python si el sistema no tiene la requerida.
- **FastAPI** en vez de Flask: validación de payloads con Pydantic "gratis",
  documentación OpenAPI autogenerada (`/docs`), asíncrono nativo.
- **JMeter** en vez de un script custom de carga: estándar de facto para "emular
  usuarios", genera reportes HTML sin código adicional.
- **pre-commit + nbstripout**: los notebooks nunca deberían commitear outputs
  binarios (figuras, tablas grandes) — infla el repo y genera diffs ilegibles.
