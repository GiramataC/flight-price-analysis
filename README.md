# ✈️ Bangladesh Flight Price Analysis Pipeline

An end-to-end data engineering pipeline built with Apache Airflow, MySQL, PostgreSQL, and dbt to process and analyze flight price data for Bangladesh. The pipeline ingests raw CSV data, validates and cleans it, transfers it to an analytics database, and computes KPIs for business insight.

> **Note:** A separate machine learning pipeline (`flight_fare_retrain`) also runs in Airflow for fare prediction. It is documented independently.

---

## 📐 Architecture Overview

```
Flight_Price_Dataset_of_Bangladesh.csv
                │
                ▼
        ┌──────────────┐
        │    ingest    │  Load CSV → MySQL staging
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │   validate   │  Clean & validate → MySQL
        └──────┬───────┘
               │
               ▼
        ┌──────────────────┐
        │ load_to_postgres │  Transfer → PostgreSQL
        └──────┬───────────┘
               │
               ▼
        ┌──────────────┐
        │   dbt_run    │  Build KPI tables
        └──────┬───────┘
               │
     ┌─────────┼──────────────┐
     ▼         ▼              ▼
kpi_avg_fare  kpi_popular  kpi_seasonal
             _routes       _variation
```

### Infrastructure

| Container | Role | Port |
|---|---|---|
| `postgres_airflow_meta` | Airflow internal metadata | 5433 |
| `mysql_staging` | Staging DB — raw and validated data | 3306 |
| `postgres_analytics` | Analytics DB — KPI tables | 5432 |
| `airflow_init` | One-shot init: DB migration + admin user | — |
| `airflow_webserver` | Airflow UI | 8080 |
| `airflow_scheduler` | DAG scheduling and task execution | — |

---

## 🗂️ Project Structure

```
flight_price_analysis/
├── dags/
│   ├── flight_pipeline_dag.py        # ETL + KPI pipeline (this project)
│   └── flight_fare_retrain_dag.py    # ML retraining pipeline (separate)
│
├── scripts/
│   ├── ingestion.py                  # CSV → MySQL
│   ├── validation.py                 # Data cleaning and validation
│   ├── load_to_postgres.py           # MySQL → PostgreSQL
│   ├── mysql_init.sql                # MySQL staging schema
│   ├── postgres_init.sql             # PostgreSQL analytics schema
│   └── flight_fare/                  # ML modules (separate pipeline)
│
├── dbt/
│   ├── dbt_project.yml
│   └── models/
│       ├── staging/
│       │   └── stg_flights.sql
│       └── marts/
│           ├── kpi_avg_fare.sql
│           ├── kpi_popular_routes.sql
│           └── kpi_seasonal_variation.sql
│
├── dbt_profiles/
│   └── profiles.yml
│
├── data/
│   └── Flight_Price_Dataset_of_Bangladesh.csv
│
├── config/
│   └── settings.py
│
└── docker-compose.yml
```

---

## 🚀 Getting Started

### Prerequisites
- Docker Desktop installed and running
- At least 4GB RAM allocated to Docker
- Ports 8080, 3306, 5432, 5433 available

### 1. Clone the repository
```bash
git clone <repo-url>
cd flight_price_analysis
```

### 2. Add the dataset
Download from [Kaggle](https://www.kaggle.com/datasets/mahatiratusher/flight-price-dataset-of-bangladesh) and place at:
```
data/Flight_Price_Dataset_of_Bangladesh.csv
```

### 3. Start all services
```bash
docker compose up -d
```

### 4. Wait for startup (~2–3 minutes)
```bash
docker logs airflow_webserver -f
# Wait for: Listening at: http://0.0.0.0:8080
```

### 5. Open Airflow UI
**http://localhost:8080** — login: `admin` / `admin`

### 6. Run the pipeline
- Toggle on `flight_pipeline`
- Click ▶ to trigger manually
- Watch all 4 tasks turn green

---

## 📊 DAG: flight_pipeline

**Schedule:** `@daily`  
**Catchup:** Disabled

### Task Flow

```
ingest >> validate >> load_to_postgres >> dbt_run
```

### Task 1 — `ingest`
Reads the CSV file, renames columns to match the staging schema, adds a `pipeline_run_id` (UUID) and `load_timestamp`, and appends all rows to MySQL `raw_flights`.

**Column mapping:**

| CSV Column | DB Column |
|---|---|
| Airline | airline |
| Source | source |
| Destination | destination |
| Departure Date & Time | departure_time |
| Arrival Date & Time | arrival_time |
| Duration (hrs) | duration |
| Stopovers | stops |
| Base Fare (BDT) | base_fare |
| Tax & Surcharge (BDT) | tax_and_surcharge |
| Total Fare (BDT) | total_fare |
| Class | booking_class |

**Output:** 57,000 rows → MySQL `raw_flights`

---

### Task 2 — `validate`
Reads rows from MySQL `raw_flights` filtered by `pipeline_run_id`, applies cleaning rules, and writes to MySQL `validated_flights`.

**Cleaning rules:**

| Rule | Implementation |
|---|---|
| Correct negative fares | `base_fare = base_fare.abs()` |
| Handle null tax values | `tax_and_surcharge = fillna(0)` |
| Recalculate total fare | `total_fare = base_fare + tax_and_surcharge` |
| Flag row status | `validation_status = "valid"` |
| SQL injection prevention | Parameterised queries via SQLAlchemy `text()` |

**Output:** 57,000 validated rows → MySQL `validated_flights`

---

### Task 3 — `load_to_postgres`
Reads validated data from MySQL `validated_flights` filtered by `pipeline_run_id` and writes it to PostgreSQL `raw_flights` for dbt to consume.

**Output:** 57,000 rows → PostgreSQL `raw_flights`

---

### Task 4 — `dbt_run`
Executes all dbt models in dependency order using `subprocess.run(["dbt", "run"], check=True)`.

**Output:** 4 tables built — PASS=4, WARN=0, ERROR=0

---

## 📐 dbt Models

### Staging

**`stg_flights`** — Clean base layer over `raw_flights`:
```sql
SELECT
    airline, source, destination,
    departure_time, arrival_time, duration, stops,
    base_fare, tax_and_surcharge, total_fare,
    booking_class, pipeline_run_id, load_timestamp
FROM raw_flights
```
→ 57,000 rows

---

### KPI Marts

**`kpi_avg_fare`** — Average fare and booking count per airline:
```sql
SELECT
    airline,
    AVG(total_fare) AS avg_fare,
    COUNT(*) AS bookings
FROM stg_flights
GROUP BY airline
```
→ 24 rows

---

**`kpi_popular_routes`** — Routes ranked by booking volume:
```sql
SELECT
    source,
    destination,
    COUNT(*) AS bookings,
    AVG(total_fare) AS avg_fare
FROM stg_flights
GROUP BY source, destination
ORDER BY bookings DESC
```
→ 152 rows

---

**`kpi_seasonal_variation`** — Fare comparison by season per airline:
```sql
SELECT
    airline,
    CASE
        WHEN EXTRACT(MONTH FROM departure_time::timestamp) IN (4, 6, 12)
        THEN 'Peak'
        ELSE 'Off-Peak'
    END AS season,
    AVG(total_fare) AS avg_fare
FROM stg_flights
GROUP BY airline, season
```
→ 48 rows

**Peak months:** April (Eid al-Fitr / Pohela Boishakh), June (Eid al-Adha), December (Winter Holidays)

---

## 📈 KPI Summary

| KPI | Table | Rows | Business Question |
|---|---|---|---|
| Average Fare by Airline | `kpi_avg_fare` | 24 | Which airlines are most/least expensive? |
| Booking Count by Airline | `kpi_avg_fare` | 24 | Which airlines have the most bookings? |
| Most Popular Routes | `kpi_popular_routes` | 152 | Which routes have the highest demand? |
| Seasonal Fare Variation | `kpi_seasonal_variation` | 48 | How much do fares rise during peak seasons? |

---

## 🗄️ Database Schema

### MySQL — `flight_staging`

**`raw_flights`**
```
id (AUTO_INCREMENT PK)
airline, source, destination
departure_time, arrival_time, duration, stops
base_fare, tax_and_surcharge, total_fare
booking_class, load_timestamp, pipeline_run_id
```

**`validated_flights`**
```
id (AUTO_INCREMENT PK), raw_id
airline, source, destination
base_fare, tax_and_surcharge, total_fare
is_peak_season, season_label
validation_status, pipeline_run_id
```

### PostgreSQL — `flight_analytics`

```
raw_flights          — analytics copy of validated data
stg_flights          — dbt staging model
kpi_avg_fare         — airline fare and booking KPI
kpi_popular_routes   — route popularity KPI
kpi_seasonal_variation — seasonal pricing KPI
```

---

## 🔍 Useful Commands

```bash
# Check all containers
docker ps

# View task logs
docker logs airflow_scheduler --tail 50

# Query KPI: average fare by airline
docker exec -it postgres_analytics psql -U airflow -d flight_analytics -c \
  "SELECT airline, ROUND(avg_fare::numeric,2) AS avg_fare, bookings
   FROM kpi_avg_fare ORDER BY avg_fare DESC;"

# Query KPI: top 10 routes
docker exec -it postgres_analytics psql -U airflow -d flight_analytics -c \
  "SELECT source, destination, bookings, ROUND(avg_fare::numeric,2)
   FROM kpi_popular_routes ORDER BY bookings DESC LIMIT 10;"

# Query KPI: seasonal variation
docker exec -it postgres_analytics psql -U airflow -d flight_analytics -c \
  "SELECT airline, season, ROUND(avg_fare::numeric,2)
   FROM kpi_seasonal_variation ORDER BY airline, season;"

# Run dbt manually
docker exec airflow_scheduler dbt run --project-dir /opt/airflow/dbt

# Full reset (removes all data)
docker compose down -v
```

---

## ⚙️ Key Dependencies

| Package | Version | Purpose |
|---|---|---|
| apache-airflow | 2.9.0 | Orchestration |
| dbt-core | 1.5.11 | Data transformation |
| dbt-postgres | 1.5.11 | dbt PostgreSQL adapter |
| pandas | 2.1.4 | DataFrame operations |
| sqlalchemy | 1.4.52 | DB connectivity |
| pymysql | 1.1.0 | MySQL driver |
| psycopg2-binary | 2.9.9 | PostgreSQL driver |
| apache-airflow-providers-mysql | 5.5.3 | Airflow MySQL hook |

---

## 📄 Data Source

**Dataset:** [Flight Price Dataset of Bangladesh — Kaggle](https://www.kaggle.com/datasets/mahatiratusher/flight-price-dataset-of-bangladesh)  
**Records:** 57,000 flight bookings  
**Airlines covered:** 24  
**Routes covered:** 152 unique source-destination pairs
