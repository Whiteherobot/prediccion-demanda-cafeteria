# Reporte ejecutivo de demanda

_Generado automáticamente el 2026-07-08 17:14_

Este reporte resume, en lenguaje simple, qué tan bien predice el sistema la demanda de cada producto y qué se espera para mañana.

## ¿Qué tan confiable es el sistema?

- En promedio, el modelo explica **41%** de las variaciones de la demanda del día siguiente (antes de esta mejora explicaba un 28%).
- Usar el modelo, en vez de simplemente repetir la venta de la semana pasada, reduciría el costo estimado por quiebres de stock y sobre-stock en un **44%** (con costos de ejemplo — se ajustará con datos reales de la empresa).

## Predicción para mañana, por producto

| Producto | Predicción | Rango esperado | Riesgo | Alerta alta demanda |
|---|---|---|---|---|
| Laptop Gamer | 11 u. | 6.87–17.31 u. | 🟡 amarillo | No |
| Monitor 4K | 13 u. | 8.78–19.22 u. | 🟡 amarillo | No |
| Teclado Mecanico | 15 u. | 10.82–21.26 u. | 🟡 amarillo | Sí |
| Raton Inal. | 16 u. | 11.85–22.29 u. | 🟡 amarillo | No |
| Cable USB-C | 20 u. | 15.56–26.0 u. | 🟡 amarillo | No |
| Adaptador HDMI | 17 u. | 12.57–23.0 u. | 🟡 amarillo | No |
| Webcam HD | 12 u. | 7.4–17.83 u. | 🟡 amarillo | No |
| Auriculares BT | 16 u. | 11.22–21.65 u. | 🟡 amarillo | No |
| Hub USB 3.0 | 11 u. | 6.16–16.59 u. | 🟡 amarillo | No |
| Cargador Rapido | 17 u. | 12.14–22.58 u. | 🟡 amarillo | No |

## ¿Qué mueve más la predicción?

- El promedio de ventas de las últimas dos semanas
- Qué día de la semana es
- Cuánto stock hay disponible
- Cuánto se vendió hoy
- Cuánto se vendió ayer

## Limitaciones actuales

- Los datos son **sintéticos** (no son las ventas reales del negocio todavía).
- Variables como promociones o clima son simuladas; con el Excel real de la empresa se recalcularán y probablemente su importancia cambie.
- Productos marcados en 🔴 no tienen suficiente historial (mínimo 30 días) — sus predicciones son menos confiables.
