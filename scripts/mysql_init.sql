CREATE TABLE IF NOT EXISTS raw_flights (
    id INT AUTO_INCREMENT PRIMARY KEY,
    airline VARCHAR(100),
    source VARCHAR(100),
    destination VARCHAR(100),
    departure_time VARCHAR(50),
    arrival_time VARCHAR(50),
    duration FLOAT,
    stops VARCHAR(50),
    base_fare DECIMAL(10,2),
    tax_and_surcharge DECIMAL(10,2),
    total_fare DECIMAL(10,2),
    booking_class VARCHAR(50),
    load_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    pipeline_run_id VARCHAR(36)
);

CREATE TABLE IF NOT EXISTS validated_flights (
    id INT AUTO_INCREMENT PRIMARY KEY,
    raw_id INT,
    airline VARCHAR(100),
    source VARCHAR(100),
    destination VARCHAR(100),
    base_fare DECIMAL(10,2),
    tax_and_surcharge DECIMAL(10,2),
    total_fare DECIMAL(10,2),
    is_peak_season TINYINT DEFAULT 0,
    season_label VARCHAR(50),
    validation_status VARCHAR(20),
    pipeline_run_id VARCHAR(36)
);