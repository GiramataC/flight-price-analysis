# Flight Price Analysis Pipeline — Project Report

## Executive Summary

An end-to-end data pipeline was built using Apache Airflow to process and analyze flight price data for Bangladesh. The pipeline ingests raw CSV data into a MySQL staging database, validates and cleans it, transfers it to PostgreSQL, and uses dbt to compute four KPI tables for analysis. All components run in Docker containers and are orchestrated by Airflow on a daily schedule.

---

## 1. Pipeline Architecture & Execution Flow

```
CSV File
   ↓
[ingest] → MySQL: raw_flights (57,000 rows)
   ↓
[validate] → MySQL: validated_flights (57,000 rows)
   ↓
[load_to_postgres] → PostgreSQL: raw_flights (57,000 rows)
   ↓
[dbt_run] → PostgreSQL: stg_flights (57,000 rows)
                       → kpi_avg_fare (24 rows)
                       → kpi_popular_routes (152 rows)
                       → kpi_seasonal_variation (48 rows)
```

### Infrastructure

| Container | Role | Port |
|---|---|---|
| `postgres_airflow_meta` | Airflow internal metadata database | 5433 |
| `mysql_staging` | Staging database for raw and validated data | 3306 |
| `postgres_analytics` | Analytics database for KPI tables | 5432 |
| `airflow_init` | One-shot init container — runs DB migrations and creates admin user | — |
| `airflow_webserver` | Airflow UI | 8080 |
| `airflow_scheduler` | DAG trigger and task monitoring | — |

---

## 2. DAG & Task Descriptions

**DAG ID:** `flight_pipeline`  
**Schedule:** `@daily`  
**Catchup:** Disabled  
**Total Tasks:** 4  

### Task 1 — `ingest`
- **Operator:** PythonOperator
- **Script:** `scripts/ingestion.py`
- **What it does:** Reads `Flight_Price_Dataset_of_Bangladesh.csv`, renames columns to match the staging schema, adds a `pipeline_run_id` (UUID) and `load_timestamp`, then writes all rows to `raw_flights` in MySQL using SQLAlchemy with `if_exists="append"`.
- **Column mapping applied:**

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

- **Output:** 57,000 rows loaded into MySQL `raw_flights`
- **XCom return:** `{"run_id": "<uuid>", "rows": 57000}`

---

### Task 2 — `validate`
- **Operator:** PythonOperator
- **Script:** `scripts/validation.py`
- **What it does:** Reads rows from MySQL `raw_flights` filtered by `pipeline_run_id`, applies cleaning rules, and writes the result to MySQL `validated_flights`.
- **Validation & cleaning rules:**

| Rule | Implementation |
|---|---|
| Remove negative fares | `base_fare = base_fare.abs()` |
| Handle null tax values | `tax_and_surcharge = fillna(0)` |
| Recalculate total fare | `total_fare = base_fare + tax_and_surcharge` |
| Flag valid rows | `validation_status = "valid"` |
| Peak season detection | `is_peak_season`, `season_label` (defaults, enriched by dbt) |
| SQL injection prevention | Parameterised queries using SQLAlchemy `text()` |

- **Output:** 57,000 validated rows written to MySQL `validated_flights`

---

### Task 3 — `load_to_postgres`
- **Operator:** PythonOperator
- **Script:** `scripts/load_to_postgres.py`
- **What it does:** Reads validated data from MySQL `validated_flights` filtered by `pipeline_run_id` and writes it to PostgreSQL `raw_flights` for dbt to consume.
- **Output:** 57,000 rows transferred to PostgreSQL

---

### Task 4 — `dbt_run`
- **Operator:** PythonOperator
- **Command:** `subprocess.run(["dbt", "run", "--project-dir", "/opt/airflow/dbt"], check=True)`
- **What it does:** Executes all dbt models in dependency order, building the staging and KPI tables in PostgreSQL.
- **Output:** 4 tables created — PASS=4, WARN=0, ERROR=0

---

## 3. dbt Models

### Project Structure
```
dbt/
├── dbt_project.yml
└── models/
    ├── staging/
    │   └── stg_flights.sql
    └── marts/
        ├── kpi_avg_fare.sql
        ├── kpi_popular_routes.sql
        └── kpi_seasonal_variation.sql
```

### Staging Layer

**`stg_flights`** — Clean base table over `raw_flights`:
```sql
SELECT
    airline, source, destination,
    departure_time, arrival_time, duration, stops,
    base_fare, tax_and_surcharge, total_fare,
    booking_class, pipeline_run_id, load_timestamp
FROM raw_flights
```
→ 57,000 rows | Materialized as table

---

### KPI Layer (marts)

**`kpi_avg_fare`** — Average fare and booking count per airline:
```sql
SELECT
    airline,
    AVG(total_fare) AS avg_fare,
    COUNT(*) AS bookings
FROM stg_flights
GROUP BY airline
```
→ 24 rows (one per airline) | Covers both "Average Fare by Airline" and "Booking Count by Airline" KPIs

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
→ 152 rows (all unique source-destination pairs)

---

**`kpi_seasonal_variation`** — Fare comparison across peak and off-peak seasons:
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
→ 48 rows (24 airlines × 2 seasons)

**Peak months defined:** April (Eid al-Fitr / Pohela Boishakh), June (Eid al-Adha), December (Winter Holidays)

---

## 4. KPI Definitions & Results

| KPI | Table | Rows | Definition |
|---|---|---|---|
| Average Fare by Airline | `kpi_avg_fare` | 24 | Mean `total_fare` grouped by airline |
| Booking Count by Airline | `kpi_avg_fare` | 24 | COUNT(*) grouped by airline |
| Most Popular Routes | `kpi_popular_routes` | 152 | Source-destination pairs ranked by booking count |
| Seasonal Fare Variation | `kpi_seasonal_variation` | 48 | Average fare split by Peak vs Off-Peak season per airline |

---

## 5. Database Schema

### MySQL — Staging (`flight_staging`)

**`raw_flights`**
```
id (AUTO_INCREMENT PK), airline, source, destination,
departure_time, arrival_time, duration, stops,
base_fare, tax_and_surcharge, total_fare,
booking_class, load_timestamp, pipeline_run_id
```

**`validated_flights`**
```
id (AUTO_INCREMENT PK), raw_id, airline, source, destination,
base_fare, tax_and_surcharge, total_fare,
is_peak_season, season_label, validation_status, pipeline_run_id
```

### PostgreSQL — Analytics (`flight_analytics`)

**`raw_flights`** — transfer target from MySQL  
**`stg_flights`** — dbt staging model  
**`kpi_avg_fare`** — airline fare and booking KPI  
**`kpi_popular_routes`** — route popularity KPI  
**`kpi_seasonal_variation`** — seasonal pricing KPI  

---

## 6. Technology Stack

| Technology | Version | Role |
|---|---|---|
| Apache Airflow | 2.9.0 | Workflow orchestration |
| MySQL | 8.0 | Staging database |
| PostgreSQL | 15 | Analytics database |
| dbt-core | 1.5.11 | Data transformation and KPI computation |
| Python | 3.12 | Data processing scripts |
| pandas | 2.1.4 | DataFrame operations |
| SQLAlchemy | 1.4.52 | Database connectivity |
| PyMySQL | 1.1.0 | MySQL Python driver |
| Docker / Docker Compose | — | Container orchestration |

---

## 7. Challenges Encountered & Resolutions

| # | Challenge | Root Cause | Resolution |
|---|---|---|---|
| 1 | `mysqlclient` failed to build | Requires C compiler not in Airflow image | Replaced with `pymysql` (pure Python driver) |
| 2 | Airflow crashed on startup | `sqlalchemy==2.0` incompatible with Airflow 2.9.0 which requires `<2.0` | Pinned to `sqlalchemy==1.4.52` |
| 3 | `dbt-core==1.8` failed to install | Dependency `logbook` had no pre-built wheel for Python 3.12 | Downgraded to `dbt-core==1.5.11` |
| 4 | `postgres_init.sql` crashed Docker init | Script contained `CREATE DATABASE` and `\c` which are invalid in SQL init files | Removed both lines — DB is created by `POSTGRES_DB` env var |
| 5 | DAG not appearing in Airflow UI | `PYTHONPATH` not set; missing `__init__.py` in `scripts/` and `dags/` | Added `PYTHONPATH=/opt/airflow`; created `__init__.py` files |
| 6 | Log processor crash loop | Stale `./logs/` folder owned by root; Airflow user couldn't write logs | Deleted logs folder; added `chown` fix in `airflow-init` command |
| 7 | `pandas.to_sql` tried to CREATE TABLE | Table pre-existed from init SQL; pandas defaulted to `if_exists="fail"` | Used `if_exists="append"` |
| 8 | CSV columns didn't match DB schema | CSV used `Base Fare (BDT)`, `Stopovers` etc. instead of snake_case names | Added `COLUMN_MAP` in `ingestion.py` to rename before insert |
| 9 | `KeyError: 'id'` in validation | `id` is a SERIAL column generated by the DB — not present in the DataFrame | Used `df.index` as `raw_id` instead |
| 10 | dbt found 0 models | SQL files were in `./models/` root, not in `./dbt/models/` | Copied models into correct dbt project directory |
| 11 | `stg_flights` referenced non-existent columns | CSV had no `id` or `travel_date` columns | Removed `id`; replaced `travel_date` with `departure_time` |
| 12 | `docker-compose.yml` syntax error | `mysql-staging` service block had no indentation | Fixed YAML indentation |

---


