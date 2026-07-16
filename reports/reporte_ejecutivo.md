# Reporte ejecutivo de demanda — El Café que te Conté

_Generado automáticamente el 2026-07-16 12:32_

Este reporte resume, en lenguaje simple, qué tan bien predice el sistema la demanda de cada producto y qué se espera para mañana. Está calculado sobre las ventas reales de la cafetería (abril-julio 2026).

## ¿Qué tan confiable es el sistema?

- En promedio, el modelo explica **46%** de las variaciones de la demanda del día siguiente.
- Usar el modelo, en vez de simplemente repetir la venta de la semana pasada, reduciría los ingresos en riesgo (por quiebre de stock o producto preparado de más) en un **33%**, calculado con los precios reales del menú.

## Predicción para mañana, por producto

| Producto | Predicción | Rango esperado | Riesgo | Alerta alta demanda |
|---|---|---|---|---|
| Affo Cookie | 10 u. | 0.59–23.83 u. | 🟡 amarillo | No |
| Agua | 28 u. | 17.97–41.21 u. | 🟡 amarillo | No |
| Avocado Toast | 12 u. | 2.1–25.34 u. | 🟡 amarillo | No |
| Bacon Egg and Cheese | 11 u. | 1.14–24.38 u. | 🟡 amarillo | No |
| Bananella Toast | 11 u. | 1.07–24.31 u. | 🟡 amarillo | No |
| Break Your Diet | 13 u. | 2.97–26.21 u. | 🟡 amarillo | Sí |
| Café | 39 u. | 29.25–52.49 u. | 🔴 rojo | No |
| Cheesecake de Frutos Rojos | 10 u. | 0.02–23.26 u. | 🟡 amarillo | No |
| Cheesecake de Limón | 11 u. | 1.22–24.46 u. | 🟡 amarillo | No |
| Chispas de Chocolate | 21 u. | 11.9–35.14 u. | 🟡 amarillo | No |
| Cómo en Casa | 11 u. | 1.62–24.86 u. | 🟡 amarillo | No |
| Frappé | 20 u. | 10.28–33.52 u. | 🟡 amarillo | No |
| Fudgy Brownies | 10 u. | 0.86–24.1 u. | 🟡 amarillo | No |
| Galleta de Nuez | 11 u. | 1.12–24.36 u. | 🟡 amarillo | No |
| Gaseosas | 44 u. | 34.11–57.35 u. | 🔴 rojo | No |
| Ham and Cheese | 11 u. | 1.56–24.8 u. | 🟡 amarillo | No |
| Helado y Nutella | 9 u. | 0.0–22.8 u. | 🟡 amarillo | No |
| Jugos | 35 u. | 25.58–48.82 u. | 🔴 rojo | No |
| Maní y Almendras | 12 u. | 2.23–25.47 u. | 🟡 amarillo | No |
| Negrito Affogato | 11 u. | 1.56–24.8 u. | 🟡 amarillo | No |
| New York Oreo | 10 u. | 0.85–24.09 u. | 🟡 amarillo | No |
| New York Triple Chocolate | 12 u. | 1.98–25.22 u. | 🟡 amarillo | No |
| Nutella French Toast | 12 u. | 2.24–25.48 u. | 🟡 amarillo | No |
| Nutella Maní | 10 u. | 0.9–24.14 u. | 🟡 amarillo | No |
| Patacón Crunch | 10 u. | 0.77–24.01 u. | 🟡 amarillo | No |
| Pizza Toast | 11 u. | 1.82–25.06 u. | 🟡 amarillo | No |
| Red Velvet | 19 u. | 9.33–32.57 u. | 🟡 amarillo | No |
| Smoothies | 34 u. | 24.12–47.36 u. | 🔴 rojo | No |
| Tigrillo Patacón | 12 u. | 2.21–25.45 u. | 🟡 amarillo | Sí |
| Torta Mojada de Chocolate | 11 u. | 1.42–24.66 u. | 🟡 amarillo | No |
| Tres Leches | 12 u. | 2.37–25.61 u. | 🟡 amarillo | No |
| Triple Chocolate | 12 u. | 2.16–25.4 u. | 🟡 amarillo | No |
| Vainilla con Relleno de Mermelada | 11 u. | 1.67–24.92 u. | 🟡 amarillo | No |

## ¿Qué mueve más la predicción?

- El promedio de ventas de las últimas dos semanas
- La categoría del producto
- El promedio de ventas de la última semana
- El precio promedio del producto ese día
- Qué tan irregulares fueron las ventas la última semana

## Limitaciones actuales

- El modelo se entrenó con 4 meses de historia (abril-julio 2026) — mientras más meses de ventas se acumulen, mejores serán las predicciones.
- No se cuenta todavía con datos de promociones ni clima; si la cafetería empieza a registrar promociones activas, se pueden incorporar para mejorar la precisión.
- Un producto sale en 🔴 por dos motivos posibles: historial insuficiente (mínimo 30 días) o porque su situación actual (ventas recientes, contexto) es distinta a lo habitual y el sistema prefiere avisar en vez de predecir con falsa confianza.
- Hoy están en 🔴 por contexto atípico (no por falta de historial): Café, Gaseosas, Jugos, Smoothies. Vale la pena revisar sus ventas de los últimos días antes de confiar en la predicción.
