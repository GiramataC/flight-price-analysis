"""
api.py
──────
Flask REST API for Flight Fare Prediction.

Endpoints:
    GET  /health          → service health check
    GET  /features        → lists expected input fields
    POST /predict         → returns predicted fare in BDT

Run:
    python api.py

Test:
    curl -X POST http://localhost:5000/predict \\
         -H "Content-Type: application/json" \\
         -d '{
               "airline": "Emirates",
               "source": "DAC",
               "destination": "DXB",
               "class": "Economy",
               "booking_source": "Direct Booking",
               "duration_hrs": 4.5,
               "stopovers": 0,
               "days_before_departure": 30,
               "departure_hour": 10,
               "departure_day": 15,
               "departure_month": 6,
               "departure_weekday": 2,
               "arrival_hour": 14
             }'
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from flask import Flask, request, jsonify

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent
MODEL_PATH  = BASE_DIR / "outputs" / "best_model_xgboost.pkl"
SCALER_PATH = BASE_DIR / "outputs" / "feature_scaler.pkl"

# ── Feature order must match exactly what splitter.py trained on ──────────────
# Derived from config.CAT_COLS + config.NUM_COLS — aircraft_type and seasonality
# excluded because they were not in the model's training features.
FEATURE_ORDER = [
    # Categorical (label-encoded at training time)
    "airline", "source", "destination",
    "class", "booking_source",
    # Numerical
    "duration_hrs", "days_before_departure", "stopovers",
    "departure_hour", "departure_day", "departure_month",
    "departure_weekday", "arrival_hour", "is_international",
]

# ── Label encoding maps (must match what splitter.py learned) ─────────────────
LABEL_MAPS = {
    "airline": sorted([
        "Air Arabia", "Air Astra", "Air India", "AirAsia",
        "Biman Bangladesh Airlines", "British Airways", "Cathay Pacific",
        "Emirates", "Etihad Airways", "FlyDubai", "Gulf Air", "IndiGo",
        "Kuwait Airways", "Lufthansa", "Malaysian Airlines", "NovoAir",
        "Qatar Airways", "Saudia", "Singapore Airlines", "SriLankan Airlines",
        "Thai Airways", "Turkish Airlines", "US-Bangla Airlines", "Vistara",
    ]),
    "source": sorted(["BZL", "CGP", "CXB", "DAC", "JSR", "RJH", "SPD", "ZYL"]),
    "destination": sorted([
        "BKK", "CCU", "CGP", "DAC", "DEL", "DXB", "JED", "JFK",
        "KUL", "KWI", "LHR", "MLE", "RJH", "SIN", "SPD",
        "TBS", "TUL", "YYZ", "ZYL", "CMB",
    ]),
    "class": sorted(["Business", "Economy", "First Class"]),
    "booking_source": sorted(["Direct Booking", "Online Website", "Travel Agency"]),
    "seasonality": sorted(["Eid", "Hajj", "Regular", "Winter Holidays"]),
}


def label_encode(col: str, value: str) -> int:
    """Replicate LabelEncoder: sorted alphabetical → index."""
    mapping = {v: i for i, v in enumerate(LABEL_MAPS[col])}
    if value not in mapping:
        raise ValueError(f"Unknown value '{value}' for '{col}'. "
                         f"Valid options: {LABEL_MAPS[col]}")
    return mapping[value]


# ── Load artefacts once at startup ────────────────────────────────────────────
app = Flask(__name__)

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

# Scaler not used for XGBoost (tree-based) but loaded for completeness
with open(SCALER_PATH, "rb") as f:
    scaler = pickle.load(f)

print(f"Model loaded: {MODEL_PATH.name}")
print(f"Scaler loaded: {SCALER_PATH.name}")


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model": "XGBoost (Gradient Boosting best)"}), 200


@app.route("/features", methods=["GET"])
def features():
    """Returns expected input fields and valid values for categoricals."""
    return jsonify({
        "required_fields": FEATURE_ORDER,
        "categorical_options": LABEL_MAPS,
        "numerical_fields": [
            "duration_hrs", "days_before_departure", "stopovers",
            "departure_hour", "departure_day", "departure_month",
            "departure_weekday", "arrival_hour",
        ],
        "note": "is_international is computed automatically from duration_hrs"
    }), 200


@app.route("/predict", methods=["POST"])
def predict():
    try:
        payload = request.get_json(force=True)

        if not payload:
            return jsonify({"error": "No JSON payload received"}), 400

        # ── Derive is_international from duration ─────────────────────────
        duration = float(payload.get("duration_hrs", 0))
        payload["is_international"] = int(duration > 3.5)

        # ── Encode categoricals ───────────────────────────────────────────
        encoded = {}
        for col in LABEL_MAPS:
            if col not in payload:
                return jsonify({"error": f"Missing field: '{col}'"}), 400
            encoded[col] = label_encode(col, str(payload[col]))

        # ── Numerical fields ──────────────────────────────────────────────
        num_fields = [
            "duration_hrs", "days_before_departure", "stopovers",
            "departure_hour", "departure_day", "departure_month",
            "departure_weekday", "arrival_hour", "is_international",
        ]
        for field in num_fields:
            if field not in payload and field != "is_international":
                return jsonify({"error": f"Missing field: '{field}'"}), 400
            encoded[field] = float(payload[field])

        # ── Build feature vector in correct order ─────────────────────────
        row = pd.DataFrame([[encoded[f] for f in FEATURE_ORDER]],
                           columns=FEATURE_ORDER)

        # ── Predict (model trained on log1p target — invert with expm1) ───
        log_pred = model.predict(row)[0]
        fare_bdt = float(np.expm1(log_pred))

        return jsonify({
            "predicted_fare_bdt": round(fare_bdt, 2),
            "predicted_fare_formatted": f"৳{fare_bdt:,.2f}",
            "inputs": {k: payload[k] for k in payload if k != "is_international"},
            "is_international": bool(payload["is_international"]),
        }), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
