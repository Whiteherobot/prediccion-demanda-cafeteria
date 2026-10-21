# Reporte ejecutivo de demanda — El Café que te Conté

_Generado automáticamente el 2026-10-21 08:50_

Este reporte resume, en lenguaje simple, qué tan bien predice el sistema la demanda de cada producto y qué se espera para mañana. Está calculado sobre las ventas reales de la cafetería (abril-julio 2026).

## ¿Qué tan confiable es el sistema?

- En promedio, el modelo explica **43%** de las variaciones de la demanda del día siguiente.
- Usar el modelo, en vez de simplemente repetir la venta de la semana pasada, reduciría los ingresos en riesgo (por quiebre de stock o producto preparado de más) en un **30%**, calculado con los precios reales del menú.

## Predicción para mañana, por producto

| Producto | Predicción | Rango esperado | Riesgo | Alerta alta demanda |
|---|---|---|---|---|
| Affo Cookie | 10 u. | 0.16–23.85 u. | 🟡 amarillo | No |
| Agua | 27 u. | 17.66–41.35 u. | 🟡 amarillo | No |
| Avocado Toast | 11 u. | 1.71–25.4 u. | 🟡 amarillo | No |
| Bacon Egg and Cheese | 11 u. | 1.31–25.0 u. | 🟡 amarillo | No |
| Bananella Toast | 10 u. | 0.84–24.53 u. | 🟡 amarillo | No |
| Break Your Diet | 12 u. | 2.23–25.93 u. | 🟡 amarillo | Sí |
| Café | 40 u. | 30.06–53.75 u. | 🔴 rojo | No |
| Cheesecake de Frutos Rojos | 10 u. | 0.73–24.42 u. | 🟡 amarillo | No |
| Cheesecake de Limón | 11 u. | 1.32–25.01 u. | 🟡 amarillo | No |
| Chispas de Chocolate | 19 u. | 9.88–33.57 u. | 🟡 amarillo | No |
| Cómo en Casa | 10 u. | 0.46–24.15 u. | 🟡 amarillo | No |
| Frappé | 20 u. | 10.52–34.22 u. | 🟡 amarillo | No |
| Fudgy Brownies | 10 u. | 0.64–24.33 u. | 🟡 amarillo | No |
| Galleta de Nuez | 9 u. | 0.0–23.46 u. | 🟡 amarillo | No |
| Gaseosas | 43 u. | 33.82–57.51 u. | 🔴 rojo | No |
| Ham and Cheese | 11 u. | 1.01–24.7 u. | 🟡 amarillo | No |
| Helado y Nutella | 10 u. | 0.27–23.96 u. | 🟡 amarillo | No |
| Jugos | 34 u. | 24.93–48.62 u. | 🔴 rojo | No |
| Maní y Almendras | 11 u. | 1.29–24.98 u. | 🟡 amarillo | No |
| Negrito Affogato | 11 u. | 0.98–24.67 u. | 🟡 amarillo | No |
| New York Oreo | 10 u. | 0.05–23.75 u. | 🟡 amarillo | No |
| New York Triple Chocolate | 10 u. | 0.71–24.4 u. | 🟡 amarillo | No |
| Nutella French Toast | 11 u. | 1.65–25.34 u. | 🟡 amarillo | No |
| Nutella Maní | 10 u. | 0.57–24.26 u. | 🟡 amarillo | No |
| Patacón Crunch | 10 u. | 0.52–24.21 u. | 🟡 amarillo | No |
| Pizza Toast | 11 u. | 1.36–25.06 u. | 🟡 amarillo | No |
| Red Velvet | 18 u. | 8.9–32.59 u. | 🟡 amarillo | No |
| Smoothies | 33 u. | 22.98–46.67 u. | 🔴 rojo | No |
| Tigrillo Patacón | 11 u. | 1.71–25.4 u. | 🟡 amarillo | No |
| Torta Mojada de Chocolate | 10 u. | 0.77–24.46 u. | 🟡 amarillo | No |
| Tres Leches | 11 u. | 1.8–25.49 u. | 🟡 amarillo | No |
| Triple Chocolate | 11 u. | 1.9–25.59 u. | 🟡 amarillo | No |
| Vainilla con Relleno de Mermelada | 10 u. | 0.28–23.97 u. | 🟡 amarillo | No |

## ¿Qué mueve más la predicción?

- El promedio de ventas de las últimas dos semanas
- La categoría del producto
- El promedio de ventas de la última semana
- Cuánto se vendió hoy
- El precio promedio del producto ese día

## Limitaciones actuales

- El modelo se entrenó con 4 meses de historia (abril-julio 2026) — mientras más meses de ventas se acumulen, mejores serán las predicciones.
- No se cuenta todavía con datos de promociones ni clima; si la cafetería empieza a registrar promociones activas, se pueden incorporar para mejorar la precisión.
- Un producto sale en 🔴 por dos motivos posibles: historial insuficiente (mínimo 30 días) o porque su situación actual (ventas recientes, contexto) es distinta a lo habitual y el sistema prefiere avisar en vez de predecir con falsa confianza.
- Hoy están en 🔴 por contexto atípico (no por falta de historial): Café, Gaseosas, Jugos, Smoothies. Vale la pena revisar sus ventas de los últimos días antes de confiar en la predicción.
