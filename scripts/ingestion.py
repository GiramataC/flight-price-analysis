# import pandas as pd
# from sqlalchemy import create_engine
# from datetime import datetime
# import uuid

# def ingest_csv_to_postgres(csv_path, postgres_uri, table_name):

#     engine = create_engine(postgres_uri)

#     df = pd.read_csv(csv_path)

#     df["pipeline_run_id"] = str(uuid.uuid4())
#     df["load_timestamp"] = datetime.utcnow()

#     df.to_sql(
#         table_name,
#         engine,
#         if_exists="append",
#         index=False
#     )

#     return {
#         "run_id": df["pipeline_run_id"].iloc[0],
#         "rows": len(df)
#     }


import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import uuid

# Map CSV columns to your DB schema
COLUMN_MAP = {
    "Airline": "airline",
    "Source": "source",
    "Destination": "destination",
    "Departure Date & Time": "departure_time",
    "Arrival Date & Time": "arrival_time",
    "Duration (hrs)": "duration",
    "Stopovers": "stops",
    "Base Fare (BDT)": "base_fare",
    "Tax & Surcharge (BDT)": "tax_and_surcharge",
    "Total Fare (BDT)": "total_fare",
    "Seasonality": "booking_class",
    "Class": "booking_class",
}

# def ingest_csv_to_postgres(csv_path, postgres_uri, table_name):
#     engine = create_engine(postgres_uri)

#     df = pd.read_csv(csv_path)

#     # Rename columns to match DB schema
#     df = df.rename(columns=COLUMN_MAP)

#     # Keep only columns that exist in raw_flights
#     expected_cols = [
#         "airline", "source", "destination", "departure_time",
#         "arrival_time", "duration", "stops", "base_fare",
#         "tax_and_surcharge", "total_fare", "booking_class"
#     ]
#     df = df[[c for c in expected_cols if c in df.columns]]

#     df["pipeline_run_id"] = str(uuid.uuid4())
#     df["load_timestamp"] = datetime.utcnow()

#     # FIX: if_exists="append" won't try to CREATE TABLE
#     df.to_sql(
#         table_name,
#         engine,
#         if_exists="append",
#         index=False
#     )

#     return {
#         "run_id": df["pipeline_run_id"].iloc[0],
#         "rows": len(df)
#     }
def ingest_csv_to_mysql(csv_path, mysql_uri, table_name):
    engine = create_engine(mysql_uri)

    df = pd.read_csv(csv_path)
    df = df.rename(columns=COLUMN_MAP)

    expected_cols = [
        "airline", "source", "destination", "departure_time",
        "arrival_time", "duration", "stops", "base_fare",
        "tax_and_surcharge", "total_fare", "booking_class"
    ]
    df = df[[c for c in expected_cols if c in df.columns]]
    df["pipeline_run_id"] = str(uuid.uuid4())
    df["load_timestamp"] = datetime.utcnow()

    df.to_sql(table_name, engine, if_exists="append", index=False)

    return {
        "run_id": df["pipeline_run_id"].iloc[0],
        "rows": len(df)
    }