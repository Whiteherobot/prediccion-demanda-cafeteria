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

**Originales (Práctica 2 / Informe SVM):** `cantidad_vendida`, `dia_semana`, `mes`,
`es_weekend`, `es_feriado`, `dias_desde_inicio`, `proporcion_stock`,
`categoria_encoded`, `lag_1`, `lag_7`, `rolling_mean_7`, `rolling_std_7`.

**Nuevas de esta práctica:**

| Variable | Qué representa |
|---|---|
| `lag_2`, `lag_14` | Demanda hace 2 y 14 días — más contexto temporal que solo 1 y 7. |
| `rolling_mean_14`, `rolling_std_14` | Media y desviación móvil a 14 días. |
| `dia_semana_sin/cos`, `mes_sin/cos` | Codificación cíclica: para un kernel RBF, el lunes (0) y el domingo (6) deberían estar "cerca", no en extremos opuestos como con un entero crudo. |
| `es_fecha_especial` | Fundación de Cuenca, Día de la Madre — relevantes para un negocio local, no son feriado nacional. |
| `temporada_seca` | Jun-sep, temporada seca en la sierra ecuatoriana. |
| `promocion_activa`, `clima_lluvia`, `flujo_clientes_estimado` | **Sintéticas.** Pedidas en `Feedback Empresas.pdf` §IV.A. No hay Excel real todavía, así que se simulan de forma independiente de la demanda ya generada (sin correlación forzada) — su importancia real se mide honestamente con permutation importance en el notebook 2. |

## Costos unitarios ilustrativos (notebook 3, métricas de negocio)

`COSTO_QUIEBRE_POR_UNIDAD` y `COSTO_SOBRESTOCK_POR_UNIDAD` (por categoría) son
**valores de ejemplo**, no datos reales de ninguna empresa — sirven para demostrar
que el pipeline puede traducir error de predicción a impacto económico. Cuando
llegue el Excel real se reemplazan por costos/márgenes reales por producto.

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
