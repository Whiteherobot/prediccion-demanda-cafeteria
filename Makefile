.PHONY: setup data train results pipeline api test loadtest lint clean precommit export-onnx

# Los notebooks dependen uno del otro: nunca en paralelo, aunque MAKEFLAGS traiga -j.
.NOTPARALLEL:

# Kernel python3 del propio venv: no depende de un kernel registrado a mano
# (ese guarda la ruta absoluta y se rompe si se mueve la carpeta).
NB_TIMEOUT := --ExecutePreprocessor.timeout=600 --ExecutePreprocessor.kernel_name=python3

setup:
	uv sync
	uv run python -m ipykernel install --user --name practica3 --display-name "Python 3 (practica3)"
	uv run nbstripout --install

data:
	uv run jupyter nbconvert --to notebook --execute --inplace $(NB_TIMEOUT) notebooks/01_data.ipynb

train:
	uv run jupyter nbconvert --to notebook --execute --inplace $(NB_TIMEOUT) notebooks/02_procesos.ipynb

results:
	uv run jupyter nbconvert --to notebook --execute --inplace $(NB_TIMEOUT) notebooks/03_resultados.ipynb

pipeline:
	$(MAKE) data
	$(MAKE) train
	$(MAKE) results

export-onnx:
	uv run python -m practica3.export_onnx

api:
	uv run uvicorn practica3.api.main:app --reload --port 8000

test:
	uv run pytest -v

loadtest:
	mkdir -p jmeter/results
	jmeter -n -t jmeter/plan_practica3.jmx -l jmeter/results/resultados.jtl -e -o jmeter/results/report

lint:
	uv run ruff check .
	uv run ruff format --check .

precommit:
	uv run pre-commit run --all-files

clean:
	uv run nbstripout notebooks/*.ipynb
	rm -rf jmeter/results/*.jtl jmeter/results/report
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache
