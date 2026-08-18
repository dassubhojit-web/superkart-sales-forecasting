import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, request

MODEL_PATH = Path(__file__).resolve().with_name("superkart_model.joblib")
MODEL = joblib.load(MODEL_PATH)

REQUIRED_COLUMNS = [
    "Product_Weight",
    "Product_Sugar_Content",
    "Product_Allocated_Area",
    "Product_MRP",
    "Store_Size",
    "Store_Location_City_Type",
    "Store_Type",
    "Product_Id_char",
    "Store_Age_Years",
    "Product_Type_Category",
]
NUMERIC_COLUMNS = [
    "Product_Weight",
    "Product_Allocated_Area",
    "Product_MRP",
    "Store_Age_Years",
]

superkart_api = Flask(__name__)


def validate_frame(frame):
    if frame.empty:
        raise ValueError("Input contains no rows.")
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    validated = frame.loc[:, REQUIRED_COLUMNS].copy()
    for column in NUMERIC_COLUMNS:
        validated[column] = pd.to_numeric(validated[column], errors="raise")
        if not np.isfinite(validated[column]).all():
            raise ValueError(f"{column} contains a non-finite value.")
    return validated


@superkart_api.get("/")
@superkart_api.get("/health")
def health():
    return jsonify({"service": "superkart-sales-api", "status": "healthy"})


@superkart_api.post("/v1/predict")
def predict_one():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be one JSON object."}), 400
    try:
        frame = validate_frame(pd.DataFrame([payload]))
        prediction = float(MODEL.predict(frame)[0])
        return jsonify({"prediction": round(prediction, 2)})
    except (TypeError, ValueError) as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        superkart_api.logger.exception("Single prediction failed")
        return jsonify({"error": "Prediction failed."}), 500


@superkart_api.post("/v1/predictbatch")
def predict_batch():
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return jsonify({"error": "Upload a CSV using multipart field 'file'."}), 400
    try:
        frame = validate_frame(pd.read_csv(upload))
        predictions = MODEL.predict(frame)
        results = [
            {"row": int(index), "predicted_sales": round(float(value), 2)}
            for index, value in enumerate(predictions)
        ]
        return jsonify({"count": len(results), "predictions": results})
    except (TypeError, ValueError, pd.errors.ParserError) as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        superkart_api.logger.exception("Batch prediction failed")
        return jsonify({"error": "Batch prediction failed."}), 500


if __name__ == "__main__":
    superkart_api.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "7860")),
        debug=False,
    )
