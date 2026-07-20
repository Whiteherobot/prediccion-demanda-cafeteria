# Reporte ejecutivo de demanda — El Café que te Conté

_Generado automáticamente el 2026-07-19 22:18_

Este reporte resume, en lenguaje simple, qué tan bien predice el sistema la demanda de cada producto y qué se espera para mañana. Está calculado sobre las ventas reales de la cafetería (abril-julio 2026).

## ¿Qué tan confiable es el sistema?

- En promedio, el modelo explica **46%** de las variaciones de la demanda del día siguiente.
- Usar el modelo, en vez de simplemente repetir la venta de la semana pasada, reduciría los ingresos en riesgo (por quiebre de stock o producto preparado de más) en un **32%**, calculado con los precios reales del menú.

## Predicción para mañana, por producto

| Producto | Predicción | Rango esperado | Riesgo | Alerta alta demanda |
|---|---|---|---|---|
| Affo Cookie | 10 u. | 0.54–24.35 u. | 🟡 amarillo | No |
| Agua | 26 u. | 17.4–41.21 u. | 🟡 amarillo | No |
| Avocado Toast | 11 u. | 2.05–25.86 u. | 🟡 amarillo | No |
| Bacon Egg and Cheese | 10 u. | 1.0–24.82 u. | 🟡 amarillo | No |
| Bananella Toast | 10 u. | 1.32–25.13 u. | 🟡 amarillo | No |
| Break Your Diet | 12 u. | 3.35–27.16 u. | 🟡 amarillo | Sí |
| Café | 38 u. | 29.35–53.17 u. | 🔴 rojo | No |
| Cheesecake de Frutos Rojos | 9 u. | 0.32–24.13 u. | 🟡 amarillo | No |
| Cheesecake de Limón | 11 u. | 1.52–25.33 u. | 🟡 amarillo | No |
| Chispas de Chocolate | 20 u. | 11.36–35.17 u. | 🟡 amarillo | No |
| Cómo en Casa | 11 u. | 1.61–25.42 u. | 🟡 amarillo | No |
| Frappé | 19 u. | 10.13–33.94 u. | 🟡 amarillo | No |
| Fudgy Brownies | 10 u. | 0.81–24.63 u. | 🟡 amarillo | No |
| Galleta de Nuez | 10 u. | 0.88–24.69 u. | 🟡 amarillo | No |
| Gaseosas | 43 u. | 34.19–58.0 u. | 🔴 rojo | No |
| Ham and Cheese | 11 u. | 1.46–25.27 u. | 🟡 amarillo | No |
| Helado y Nutella | 9 u. | 0.0–23.53 u. | 🟡 amarillo | No |
| Jugos | 34 u. | 25.25–49.06 u. | 🔴 rojo | No |
| Maní y Almendras | 11 u. | 2.33–26.14 u. | 🟡 amarillo | No |
| Negrito Affogato | 11 u. | 1.65–25.46 u. | 🟡 amarillo | No |
| New York Oreo | 10 u. | 0.7–24.51 u. | 🟡 amarillo | No |
| New York Triple Chocolate | 11 u. | 1.71–25.52 u. | 🟡 amarillo | No |
| Nutella French Toast | 12 u. | 2.51–26.32 u. | 🟡 amarillo | No |
| Nutella Maní | 10 u. | 1.02–24.84 u. | 🟡 amarillo | No |
| Patacón Crunch | 10 u. | 1.17–24.98 u. | 🟡 amarillo | No |
| Pizza Toast | 11 u. | 2.05–25.86 u. | 🟡 amarillo | No |
| Red Velvet | 18 u. | 9.07–32.88 u. | 🟡 amarillo | No |
| Smoothies | 33 u. | 23.81–47.62 u. | 🔴 rojo | No |
| Tigrillo Patacón | 11 u. | 2.13–25.94 u. | 🟡 amarillo | Sí |
| Torta Mojada de Chocolate | 11 u. | 1.62–25.44 u. | 🟡 amarillo | No |
| Tres Leches | 12 u. | 2.51–26.32 u. | 🟡 amarillo | No |
| Triple Chocolate | 11 u. | 2.02–25.83 u. | 🟡 amarillo | No |
| Vainilla con Relleno de Mermelada | 11 u. | 1.66–25.47 u. | 🟡 amarillo | No |

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
