-- ============================================================
--  MySQL Staging Database Initialisation
--  Flight Price Dataset of Bangladesh
-- ============================================================

CREATE DATABASE IF NOT EXISTS flight_staging
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE flight_staging;

-- ─── Raw Ingestion Table ─────────────────────────────────────
-- Mirrors the CSV structure exactly; all columns nullable on
-- first load so bad rows are captured rather than rejected.
CREATE TABLE IF NOT EXISTS raw_flight_prices (
    id                  BIGINT          NOT NULL AUTO_INCREMENT,
    airline             VARCHAR(100),
    source              VARCHAR(100),
    destination         VARCHAR(100),
    departure_time      VARCHAR(50),
    arrival_time        VARCHAR(50),
    duration            VARCHAR(50),
    stops               VARCHAR(50),
    base_fare           DECIMAL(12, 2),
    tax_and_surcharge   DECIMAL(12, 2),
    total_fare          DECIMAL(12, 2),
    travel_date         VARCHAR(50),
    booking_class       VARCHAR(50),
    load_timestamp      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    pipeline_run_id     VARCHAR(100),
    PRIMARY KEY (id),
    INDEX idx_airline   (airline),
    INDEX idx_route     (source, destination),
    INDEX idx_run       (pipeline_run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Validated / Cleaned Staging Table ───────────────────────
CREATE TABLE IF NOT EXISTS validated_flight_prices (
    id                  BIGINT          NOT NULL AUTO_INCREMENT,
    raw_id              BIGINT,                        -- FK back to raw table
    airline             VARCHAR(100)    NOT NULL,
    source              VARCHAR(100)    NOT NULL,
    destination         VARCHAR(100)    NOT NULL,
    departure_time      VARCHAR(50),
    arrival_time        VARCHAR(50),
    duration_minutes    INT,
    stops               TINYINT         DEFAULT 0,
    base_fare           DECIMAL(12, 2)  NOT NULL,
    tax_and_surcharge   DECIMAL(12, 2)  NOT NULL DEFAULT 0,
    total_fare          DECIMAL(12, 2)  NOT NULL,
    travel_date         DATE,
    booking_class       VARCHAR(50),
    is_peak_season      TINYINT(1)      DEFAULT 0,
    season_label        VARCHAR(50),
    validation_status   ENUM('valid','corrected','flagged') DEFAULT 'valid',
    validation_notes    TEXT,
    load_timestamp      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    pipeline_run_id     VARCHAR(100),
    PRIMARY KEY (id),
    INDEX idx_airline   (airline),
    INDEX idx_route     (source, destination),
    INDEX idx_season    (is_peak_season),
    INDEX idx_date      (travel_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Validation Audit Log ────────────────────────────────────
CREATE TABLE IF NOT EXISTS validation_audit (
    id              BIGINT          NOT NULL AUTO_INCREMENT,
    pipeline_run_id VARCHAR(100),
    check_name      VARCHAR(200)    NOT NULL,
    check_result    ENUM('PASS','FAIL','WARN') NOT NULL,
    records_checked INT             DEFAULT 0,
    records_failed  INT             DEFAULT 0,
    details         TEXT,
    checked_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── Pipeline Run Log ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id          VARCHAR(100)    NOT NULL,
    dag_run_id      VARCHAR(200),
    start_time      TIMESTAMP,
    end_time        TIMESTAMP,
    status          ENUM('running','success','failed') DEFAULT 'running',
    rows_ingested   INT             DEFAULT 0,
    rows_validated  INT             DEFAULT 0,
    rows_rejected   INT             DEFAULT 0,
    notes           TEXT,
    PRIMARY KEY (run_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;