# Glosario y decisiones de arquitectura

## Términos de modelado

| Término | Significado |
|---|---|
| **SVR** (Support Vector Regression) | Regresión por vectores de soporte: ajusta la demanda dentro de un tubo de ancho `epsilon`, penalizando solo los puntos que quedan fuera. |
| **SVC** (Support Vector Classification) | Igual que SVR pero para clasificación; aquí se usa para la alerta binaria "día de alta demanda". |
| **Kernel RBF** | Función de similitud (Radial Basis Function) que permite al SVR/SVC capturar relaciones no lineales entre features y demanda. |
| **`C`, `gamma`, `epsilon`** | Hiperparámetros del SVR/SVC: `C` controla la tolerancia a errores de entrenamiento, `gamma` el alcance de cada punto de soporte, `epsilon` el ancho del tubo sin penalización. |
| **`TimeSeriesSplit`** | Validación cruzada para series de tiempo: cada fold entrena con el pasado y valida con el futuro inmediato, nunca al revés. |
| **RMSE / MAE / R²** | Métricas técnicas de error: RMSE penaliza más los errores grandes, MAE es el error absoluto promedio, R² es la proporción de varianza explicada (1 = perfecto). |
| **Horizonte (`t+1`, `t+3`, `t+7`)** | Cuántos días adelante se predice, tomando como referencia el último día con datos conocidos. |
| **Intervalo empírico (p10/p50/p90)** | En vez de asumir una distribución (ej. normal), se usan los percentiles reales de los residuos de test para construir los escenarios conservador/esperado/optimista. |
| **Permutation importance** | Mide cuánto empeora el modelo si se baraja (permuta) una sola columna — una forma de importancia de variables que funciona con cualquier modelo, no solo árboles. |
| **`IsolationForest`** | Modelo no supervisado que aísla puntos "raros" con menos particiones que el resto — aquí, combinaciones de contexto poco frecuentes (compras atípicas). |
| **Fuga de datos (*data leakage*)** | Usar información del futuro para predecir el pasado. Se evita con `shift(1)` en lags/rolling y con splits por fecha, nunca aleatorios. |

## Variables del dataset (`src/practica3/features.py`)

**Calendario e historia temporal:** `cantidad_vendida`, `dia_semana`, `mes`,
`es_weekend`, `es_feriado`, `dias_desde_inicio`, `categoria_encoded`, `lag_1`,
`lag_2`, `lag_7`, `lag_14`, `rolling_mean_7/14`, `rolling_std_7/14`,
`dia_semana_sin/cos`, `mes_sin/cos`, `es_fecha_especial`, `temporada_seca`.

**Reales, del export de ventas** (reemplazan a las sintéticas de la primera
iteración de esta práctica):

| Variable | Qué representa |
|---|---|
| `precio_promedio` | Precio unitario real promedio del producto ese día (varía si se vendió a distintos precios por variante). |
| `n_tickets_dia` | Tráfico real de clientes: número de tickets distintos ese día (todo el negocio, no por producto). |
| `hora_promedio_venta` | Hora promedio (0-24) en que se vendió el producto ese día — útil para diferenciar ítems de desayuno vs media tarde. |

**Retiradas** (tenía la iteración sintética, no hay respaldo real en `ventas.csv`):
`proporcion_stock` (no hay inventario en el export), `promocion_activa` y
`clima_lluvia` (no hay esas columnas — si la cafetería empieza a registrar
promociones o el clima, se pueden reincorporar).

## `feature_cols_svr` vs `feature_cols_svc_iso`

El notebook 2 guarda **dos** listas de features en `metadata.json`, no una:

- `feature_cols_svr`: subconjunto podado por `permutation_importance` sobre el
  SVR — las que sí ayudan a predecir la cantidad exacta.
- `feature_cols_svc_iso`: las 24 candidatas completas, usadas por el SVC de
  alerta y el `IsolationForest`. Se comprobó que reusar `feature_cols_svr` para
  el SVC bajaba su AUC de 0.62 a 0.57 — la poda optimizada para
  regresión no sirve para clasificación (ver `docs/01_arquitectura.md`).

`src/practica3/inference.py` arma un vector de entrada distinto para cada modelo
según corresponda — no es un detalle interno ignorable, es la diferencia entre una
alerta de alta demanda que funciona y una que no.

## Ingresos en riesgo (notebook 3, métricas de negocio)

A diferencia de la primera iteración (que usaba costos de ejemplo inventados por
categoría), ahora hay `precio_unitario` **real** por producto. La métrica de
negocio es directa, sin inventar márgenes: `error de predicción × precio real`.
Cuando el modelo predice **menos** de lo que realmente se vendió, se interpreta
como demanda no atendida (ingreso perdido); cuando predice **de más**, como
producto preparado de más (riesgo de merma — relevante para los productos
perecederos de la cafetería, ver `Feedback Empresas.pdf` §III.A). No se distingue
margen de costo, se usa el precio de venta como proxy único — es una
simplificación declarada, no un cálculo contable exacto.

## Por qué estas decisiones de arquitectura

- **`src/practica3/` en vez de todo el código dentro de los notebooks**: el
  notebook 2 y la API necesitan exactamente las mismas features. Duplicar esa
  lógica en dos lugares es la fuente más común de bugs silenciosos en ML
  ("funciona en el notebook pero la API predice distinto").
- **Un JSON de metadata por corrida (`models/metadata.json`)** en vez de solo
  guardar los `.joblib`: permite auditar con qué hiperparámetros y sobre qué
  métricas se entrenó cada modelo sin tener que re-ejecutar nada.
- **Semáforo de riesgo (verde/amarillo/rojo)** en vez de solo el número: la
  retroalimentación empresarial (`Feedback Empresas.pdf` §IV.B) fue explícita en
  que las empresas necesitan entender la predicción sin conocer estadística.
