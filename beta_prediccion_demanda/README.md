# Beta Predicción de Demanda — Práctica 3 (Aprendizaje Automático)

Beta standalone que conecta la API real de Práctica 3 (SVR multi-horizonte) con
una interfaz Angular con la misma estética del POS/ERP de El Café Que Te Conté.
Es un proyecto aparte, para probar la integración modelo→UI de forma aislada,
no forma parte del repo real del ECQTC.

## Requisitos

- Backend: `uv` (gestor de paquetes Python) — ver `../README.md` de `Practica_3/`.
- Frontend: Node.js 20+ y `npm`.

## 1. Levantar el backend (API real, puerto 8000)

Desde `Practica_3/` (un nivel arriba de esta carpeta):

```bash
uv sync          # instala dependencias (solo la primera vez)
make api         # uvicorn --reload en http://localhost:8000
```

Si `models/` no existe todavía (repo recién clonado sin los artefactos entrenados),
generarlos primero con:

```bash
make pipeline    # corre los 3 notebooks (01_data, 02_procesos, 03_resultados)
```

## 2. Levantar el frontend (esta carpeta, puerto 4200)

```bash
npm install      # instala dependencias (solo la primera vez)
npm start        # equivalente a `ng serve`, en http://localhost:4200
```

Abrir `http://localhost:4200` con el backend ya corriendo en el puerto 8000
(CORS ya está habilitado en la API para ese origen).

## Qué incluye

- Predicción real (SVR t+1/t+3/t+7) por producto, con escenarios y alertas.
- KPI de valor de negocio (ahorro real del modelo vs. baseline ingenuo) y
  explicación SHAP on-demand por producto (drill-down).
- Modo demo/autoplay que recorre el histórico real día a día.
- Reporte conciso de qué producto necesita más preparación (semana/mes).
- Insumos a preparar: predicción real × receta por producto (nombres de insumo
  reales del catálogo de El Café Que Te Conté; cantidades por unidad estimadas
  — badge visible en la UI, ver `src/app/core/data/recipes.ts`).
- Carga de un CSV de ventas nuevas para reentrenar los modelos on-demand.

## Desarrollo (Angular CLI estándar)

```bash
ng build   # build de producción en dist/
ng test    # unit tests (Vitest)
```
