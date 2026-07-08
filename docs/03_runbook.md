# Runbook — setup y solución de problemas

## Setup inicial

```bash
# 1. Instalar uv (una sola vez, a nivel de sistema)
sudo pacman -S uv                      # CachyOS/Arch, repo oficial
# alternativa universal: curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Instalar dependencias del proyecto (crea .venv automáticamente)
cd Practica_3
make setup                              # uv sync + registra el kernel de Jupyter + nbstripout

# 3. Ejecutar el pipeline completo (datos -> entrenamiento -> resultados)
make pipeline

# 4. Levantar la API
make api                                # http://localhost:8000/docs

# 5. (opcional) Probar carga con JMeter
sudo pacman -S --needed jdk-openjdk     # o: yay -S jmeter (instala java como dependencia)
yay -S jmeter
make loadtest
```

## Solución de problemas

**`uv: command not found`**
No está instalado. Repo oficial CachyOS: `sudo pacman -S uv`. En otras distros:
`curl -LsSf https://astral.sh/uv/install.sh | sh` y reabrir la terminal.

**`uv sync` no encuentra una versión de Python compatible**
El proyecto pide Python ≥3.11. Si el sistema no tiene una versión adecuada, `uv`
puede descargar una propia sin sudo: `uv python install 3.12` y volver a correr
`uv sync`.

**`ModuleNotFoundError` corriendo un notebook fuera de `make`**
Los notebooks asumen el kernel de `.venv` (creado por `uv sync`). Si Jupyter no lo
lista: `uv run python -m ipykernel install --user --name practica3` y seleccionar
el kernel "Python 3 (practica3)" en el notebook.

**¿Por qué esta práctica no necesita TensorFlow, a diferencia de `Practica_2/requirements.txt`?**
La Práctica 2 entrenaba un LSTM (Keras/TensorFlow) además de boosting. Esta
práctica se construye sobre el Informe SVM, que reemplazó el LSTM por
`scikit-learn` (SVR/SVC) — más simple, determinista y suficiente para el tamaño de
este dataset. No hay dependencia de TensorFlow ni de GPU en ningún punto.

**`jmeter: command not found` / falla por falta de Java**
JMeter no está en los repos oficiales de Arch/CachyOS, solo en AUR:
`yay -S jmeter` (trae `java-environment` como dependencia). Verificar con
`java -version` antes de `make loadtest`.

**El puerto 8000 ya está en uso al correr `make api`**
`uv run uvicorn practica3.api.main:app --port 8001` (o cualquier puerto libre).

**`nbstripout` no limpia los notebooks al hacer commit**
Falta registrarlo en este repositorio: `uv run nbstripout --install` (ya lo hace
`make setup`, pero si se clonó el repo de nuevo hay que repetirlo). Verificar con
`uv run nbstripout --status`.

**Un notebook fallа al ejecutarse con `nbconvert --execute` pero funciona interactivo**
Casi siempre es orden de celdas: `nbconvert --execute` corre de arriba hacia abajo
una sola vez. Si se editó una celda fuera de orden en Jupyter, reiniciar el kernel
y "Run All" antes de confiar en el resultado.

**`GridSearchCV` tarda mucho**
Con ~2800 filas de entrenamiento (33 productos × ~97 días) y grid de 48
combinaciones × `TimeSeriesSplit(5)` × 3 horizontes, `02_procesos.ipynb` debería
tardar bajo un minuto en cualquier CPU moderna. Si tarda más, revisar que
`n_jobs=-1` esté activo y que no haya otro proceso pesado corriendo (por ejemplo,
otro `make pipeline` en paralelo).

**Los tests de la API fallan con "modelo no encontrado"**
`tests/test_api.py` necesita que `models/` ya exista — correr `make pipeline`
(o al menos `make train`) antes de `make test`.

## Actualizar con un nuevo export de ventas

Cuando la cafetería mande un `ventas.csv` más reciente (más meses de historia):

1. Reemplazar `data/raw/ventas.csv` con el nuevo export (mismo esquema: `id_ticket`,
   `fecha_completa`, `hora_exacta`, `dia_de_la_semana`, `mes`, `categoria`,
   `producto`, `variante_o_sabor`, `cantidad_vendida`, `precio_unitario`,
   `total_linea`).
2. Si el rango de fechas cambia, revisar `FERIADOS_NACIONALES` y
   `FECHAS_ESPECIALES` en `src/practica3/features.py` — están calculados para
   2026-04-01 a 2026-07-31; un export con más meses puede necesitar sumar más
   feriados (ej. 10 de agosto, 9 de octubre, 3 de noviembre, 25 de diciembre).
3. `make pipeline` — todo se recalcula (features, selección, entrenamiento,
   métricas, reporte ejecutivo) sin tocar código.
