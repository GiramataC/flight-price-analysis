# import pandas as pd
# from sqlalchemy import create_engine, text

# def load_to_postgres(mysql_uri, postgres_uri, source_table, target_table, run_id):
#     mysql_engine = create_engine(mysql_uri)
#     pg_engine = create_engine(postgres_uri)

#     with mysql_engine.connect() as conn:
#         df = pd.read_sql(
#             text(f"SELECT * FROM {source_table} WHERE pipeline_run_id = :run_id"),
#             conn,
#             params={"run_id": run_id}
#         )

#     df.to_sql(target_table, pg_engine, if_exists="append", index=False)

#     return {"rows_transferred": len(df)}

import pandas as pd
from sqlalchemy import create_engine, text

def load_to_postgres(mysql_uri, postgres_uri, source_table, target_table, run_id):
    mysql_engine = create_engine(mysql_uri)
    pg_engine = create_engine(postgres_uri)

    with mysql_engine.connect() as conn:
        df = pd.read_sql(
            text(f"SELECT * FROM {source_table} WHERE pipeline_run_id = :run_id"),
            conn,
            params={"run_id": run_id}
        )

    # Keep only columns that exist in PostgreSQL raw_flights
    pg_cols = [
        "airline", "source", "destination",
        "base_fare", "tax_and_surcharge", "total_fare",
        "pipeline_run_id"
    ]
    df = df[[c for c in pg_cols if c in df.columns]]

    df.to_sql(target_table, pg_engine, if_exists="append", index=False)

    return {"rows_transferred": len(df)}