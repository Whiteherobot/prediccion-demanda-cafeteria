# Arquitectura

## Flujo de datos y componentes

```
data/raw/*.csv (copia de Práctica_2, sintético)
        │
        ▼
notebooks/01_data.ipynb ──uses──▶ src/practica3/features.py
        │  (EDA, 25 features, calidad de datos, targets multi-horizonte)
        ▼
data/processed/{dataset_features.parquet, features.json, data_quality_report.json}
        │
        ▼
notebooks/02_procesos.ipynb ──uses──▶ src/practica3/features.py
        │  (SVR x3 horizontes, SVC alerta, IsolationForest, intervalos, importancia)
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
| `src/practica3/features.py` | Construcción del dataset diario, las 25 features y el split temporal. Sin estado, sin I/O de red. |
| `src/practica3/inference.py` | Carga los artefactos de `models/` y expone `DemandPredictor.predecir()`: punto estimado, escenarios, riesgo, alertas. |
| `src/practica3/api/` | FastAPI: expone `inference.py` por HTTP. Sin lógica de negocio propia — es una capa delgada. |
| `notebooks/01_data.ipynb` | Datos: carga, EDA, features, calidad de datos, targets. |
| `notebooks/02_procesos.ipynb` | Entrenamiento: SVR multi-horizonte, SVC, anomalías, intervalos. |
| `notebooks/03_resultados.ipynb` | Resultados: métricas técnicas y de negocio, gráficos, reportes. |
| `jmeter/plan_practica3.jmx` | Simula usuarios concurrentes contra `/health` y `/predict`. |

## Por qué SVR y no LSTM/boosting

La Práctica 2 entrenó LSTM + boosting (R²=0.28 en test). El Informe SVM mostró que,
sobre el **mismo dataset pequeño** (1800 filas), un SVR simple con
`StandardScaler + GridSearchCV` iguala o supera a esos modelos (R²≈0.42) siendo
determinista, sin GPU y mucho más liviano de mantener — justo lo que necesita una
empresa pequeña sin infraestructura de ML (ver `Feedback Empresas.pdf`, donde dos de
las tres empresas contactadas ni siquiera tienen registros digitales). Esta práctica
continúa esa línea: se apuesta por mejorar el SVR vía **mejores features y mejor
manejo de la incertidumbre**, no por modelos más pesados.

## Por qué un dataset por horizonte en vez de un solo modelo recursivo

Predecir `t+3` o `t+7` encadenando 3-7 veces un modelo de `t+1` (forecast
recursivo) acumula error en cada paso. Con un dataset de 180 días por producto,
entrenar un SVR independiente por horizonte (mismo set de features, target
distinto) es más simple, más rápido de auditar y evita esa acumulación.

## Decisiones de infraestructura

- **`uv`** en vez de `pip`/`conda`: lockfile reproducible, instalación rápida,
  gestiona su propia versión de Python si el sistema no tiene la requerida.
- **FastAPI** en vez de Flask: validación de payloads con Pydantic "gratis",
  documentación OpenAPI autogenerada (`/docs`), asíncrono nativo.
- **JMeter** en vez de un script custom de carga: estándar de facto para "emular
  usuarios", genera reportes HTML sin código adicional.
- **pre-commit + nbstripout**: los notebooks nunca deberían commitear outputs
  binarios (figuras, tablas grandes) — infla el repo y genera diffs ilegibles.
