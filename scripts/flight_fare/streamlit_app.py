"""
streamlit_app.py
────────────────
Streamlit UI for Flight Fare Prediction.

Run:
    streamlit run streamlit_app.py

Requires:
    - outputs/best_model_xgboost.pkl
    - outputs/feature_scaler.pkl
    Both produced by running: python main.py
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Flight Fare Predictor — Bangladesh",
    page_icon="✈",
    layout="wide",
)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent
MODEL_PATH  = BASE_DIR / "outputs" / "best_model_xgboost.pkl"
SCALER_PATH = BASE_DIR / "outputs" / "feature_scaler.pkl"

FEATURE_ORDER = [
    "airline", "source", "destination", "class", "booking_source",
    "duration_hrs", "days_before_departure", "stopovers",
    "departure_hour", "departure_day", "departure_month",
    "departure_weekday", "arrival_hour", "is_international",
]

AIRLINES = sorted([
    "Air Arabia", "Air Astra", "Air India", "AirAsia",
    "Biman Bangladesh Airlines", "British Airways", "Cathay Pacific",
    "Emirates", "Etihad Airways", "FlyDubai", "Gulf Air", "IndiGo",
    "Kuwait Airways", "Lufthansa", "Malaysian Airlines", "NovoAir",
    "Qatar Airways", "Saudia", "Singapore Airlines", "SriLankan Airlines",
    "Thai Airways", "Turkish Airlines", "US-Bangla Airlines", "Vistara",
])

AIRPORTS = {
    "BZL": "Barisal", "CGP": "Chittagong", "CXB": "Cox's Bazar",
    "DAC": "Dhaka", "JSR": "Jessore", "RJH": "Rajshahi",
    "SPD": "Saidpur", "ZYL": "Sylhet",
}

DESTINATIONS = sorted([
    "BKK", "CCU", "CGP", "DAC", "DEL", "DXB", "JED", "JFK",
    "KUL", "KWI", "LHR", "MLE", "RJH", "SIN", "SPD",
    "TBS", "TUL", "YYZ", "ZYL", "CMB",
])

SEASONS = ["Regular", "Eid", "Hajj", "Winter Holidays"]

LABEL_MAPS = {
    "airline":        AIRLINES,
    "source":         sorted(AIRPORTS.keys()),
    "destination":    DESTINATIONS,
    "class":          sorted(["Business", "Economy", "First Class"]),
    "booking_source": sorted(["Direct Booking", "Online Website", "Travel Agency"]),
}


def label_encode(col, value):
    mapping = {v: i for i, v in enumerate(LABEL_MAPS[col])}
    return mapping[value]


# ── Load model ────────────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

@st.cache_resource
def load_scaler():
    with open(SCALER_PATH, "rb") as f:
        return pickle.load(f)


model  = load_model()
scaler = load_scaler()


# ── UI ────────────────────────────────────────────────────────────────────────
st.title("✈ Flight Fare Predictor")
st.caption("Bangladesh domestic & international routes — powered by Gradient Boosting (R² = 0.89)")

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Route")
    airline  = st.selectbox("Airline", AIRLINES, index=AIRLINES.index("Emirates"))
    source   = st.selectbox(
        "Departure Airport",
        list(AIRPORTS.keys()),
        format_func=lambda x: f"{x} — {AIRPORTS[x]}",
        index=list(AIRPORTS.keys()).index("DAC")
    )
    destination = st.selectbox("Destination", DESTINATIONS, index=DESTINATIONS.index("DXB"))

with col2:
    st.subheader("Flight Details")
    travel_class    = st.selectbox("Class", ["Economy", "Business", "First Class"])
    booking_source  = st.selectbox("Booking Source", ["Direct Booking", "Online Website", "Travel Agency"])
    seasonality     = st.selectbox("Season (context only)", SEASONS)
    stopovers       = st.selectbox("Stopovers", [0, 1, 2], format_func=lambda x: ["Direct", "1 Stop", "2 Stops"][x])

with col3:
    st.subheader("Timing")
    duration_hrs         = st.slider("Flight Duration (hrs)", 0.5, 16.0, 4.5, step=0.5)
    days_before_departure = st.slider("Days Before Departure", 1, 90, 30)
    departure_hour       = st.slider("Departure Hour", 0, 23, 10)
    arrival_hour         = st.slider("Arrival Hour", 0, 23, 14)
    departure_day        = st.slider("Departure Day", 1, 31, 15)
    departure_month      = st.slider("Departure Month", 1, 12, 6)
    departure_weekday    = st.selectbox(
        "Departure Weekday",
        [0, 1, 2, 3, 4, 5, 6],
        format_func=lambda x: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][x]
    )

st.divider()

# ── Predict ───────────────────────────────────────────────────────────────────
if st.button("🔮 Predict Fare", type="primary", use_container_width=True):
    is_international = int(duration_hrs > 3.5)

    raw = {
        "airline":        airline,
        "source":         source,
        "destination":    destination,
        "class":          travel_class,
        "booking_source": booking_source,
        "duration_hrs":   duration_hrs,
        "days_before_departure": days_before_departure,
        "stopovers":      stopovers,
        "departure_hour": departure_hour,
        "departure_day":  departure_day,
        "departure_month": departure_month,
        "departure_weekday": departure_weekday,
        "arrival_hour":   arrival_hour,
        "is_international": is_international,
    }

    # Encode
    encoded = {}
    for col in LABEL_MAPS:
        encoded[col] = label_encode(col, raw[col])
    for col in ["duration_hrs", "days_before_departure", "stopovers",
                "departure_hour", "departure_day", "departure_month",
                "departure_weekday", "arrival_hour", "is_international"]:
        encoded[col] = float(raw[col])

    row = pd.DataFrame([[encoded[f] for f in FEATURE_ORDER]], columns=FEATURE_ORDER)

    log_pred = model.predict(row)[0]
    fare     = float(np.expm1(log_pred))

    # ── Result display ────────────────────────────────────────────────────────
    st.divider()
    res_col1, res_col2, res_col3 = st.columns(3)

    with res_col1:
        st.metric("Predicted Fare", f"৳{fare:,.2f}")
    with res_col2:
        st.metric("Route", f"{source} → {destination}")
    with res_col3:
        st.metric("Flight Type", "International ✈" if is_international else "Domestic 🛫")

    # ── Fare breakdown context ────────────────────────────────────────────────
    st.divider()
    st.subheader("Context")

    season_multipliers = {"Regular": 1.0, "Winter Holidays": 1.17, "Eid": 1.34, "Hajj": 1.43}
    class_labels       = {"Economy": "lowest tier", "Business": "mid tier", "First Class": "premium tier"}

    st.info(
        f"**{seasonality}** season typically adds a "
        f"**{(season_multipliers[seasonality]-1)*100:.0f}% premium** over regular fares. "
        f"**{travel_class}** is the {class_labels[travel_class]}. "
        f"Flight duration of **{duration_hrs}hrs** classifies this as an "
        f"**{'international' if is_international else 'domestic'}** route."
    )

    with st.expander("Show raw feature vector"):
        st.dataframe(row)

