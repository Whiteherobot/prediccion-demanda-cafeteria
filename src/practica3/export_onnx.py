"""Exporta los SVR (svr_h1/h3/h7) de models/*.joblib a ONNX, para el entregable
que pide el modelo optimizado en formato .h5 o .onnx (sklearn no tiene .h5;
.onnx es el equivalente real). Verifica numéricamente contra el .joblib antes
de guardar, sobre una muestra real del dataset procesado.
"""

import json
from pathlib import Path

import joblib
import numpy as np
import onnxruntime as ort
from skl2onnx import to_onnx
from skl2onnx.common.data_types import FloatTensorType

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "dataset_features.parquet"
HORIZONTES = ["h1", "h3", "h7"]
# ONNX corre el kernel RBF en float32 vs. float64 de sklearn; la diferencia queda
# en milésimas de unidad vendida (RMSE del modelo es ~11), no afecta la predicción.
TOL = 0.05


def _muestra_features(feature_cols: list[str], n: int = 50) -> np.ndarray:
    import pandas as pd

    df = pd.read_parquet(DATA_PATH)
    return df[feature_cols].tail(n).to_numpy(dtype=np.float32)


def exportar(horizonte: str, feature_cols: list[str]) -> Path:
    pipeline = joblib.load(MODELS_DIR / f"svr_{horizonte}.joblib")
    X = _muestra_features(feature_cols)

    onnx_model = to_onnx(pipeline, initial_types=[("input", FloatTensorType([None, X.shape[1]]))])

    pred_sklearn = pipeline.predict(X)
    sess = ort.InferenceSession(onnx_model.SerializeToString(), providers=["CPUExecutionProvider"])
    pred_onnx = sess.run(None, {"input": X})[0].ravel()

    max_diff = float(np.max(np.abs(pred_sklearn - pred_onnx)))
    if max_diff > TOL:
        raise RuntimeError(
            f"svr_{horizonte}: ONNX difiere de sklearn (max_diff={max_diff:.6f} > {TOL})"
        )

    out_path = MODELS_DIR / f"svr_{horizonte}.onnx"
    out_path.write_bytes(onnx_model.SerializeToString())
    print(f"svr_{horizonte}.onnx OK (max_diff={max_diff:.6f}, n={len(X)} filas de verificación)")
    return out_path


def main() -> None:
    meta = json.loads((MODELS_DIR / "metadata.json").read_text())
    feature_cols = meta["feature_cols_svr"]
    for h in HORIZONTES:
        exportar(h, feature_cols)


if __name__ == "__main__":
    main()
