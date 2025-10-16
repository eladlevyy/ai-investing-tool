-- Create symbol_map table
CREATE TABLE IF NOT EXISTS market_data.symbol_map (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255),
    exchange VARCHAR(50),
    asset_type VARCHAR(50) DEFAULT 'equity',
    sector VARCHAR(100),
    industry VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    data_source VARCHAR(50) DEFAULT 'yfinance',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_symbol_map_symbol ON market_data.symbol_map(symbol);

-- Create bars table (will be converted to hypertable)
DROP TABLE IF EXISTS market_data.bars CASCADE;
CREATE TABLE market_data.bars (
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume BIGINT NOT NULL,
    adjusted_close DOUBLE PRECISION,
    split_adjusted BOOLEAN NOT NULL DEFAULT FALSE,
    dividend_adjusted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (symbol, timestamp),
    CONSTRAINT ck_bars_open_positive CHECK (open > 0),
    CONSTRAINT ck_bars_high_positive CHECK (high > 0),
    CONSTRAINT ck_bars_low_positive CHECK (low > 0),
    CONSTRAINT ck_bars_close_positive CHECK (close > 0),
    CONSTRAINT ck_bars_volume_non_negative CHECK (volume >= 0),
    CONSTRAINT ck_bars_high_gte_low CHECK (high >= low),
    CONSTRAINT ck_bars_high_gte_open CHECK (high >= open),
    CONSTRAINT ck_bars_high_gte_close CHECK (high >= close),
    CONSTRAINT ck_bars_low_lte_open CHECK (low <= open),
    CONSTRAINT ck_bars_low_lte_close CHECK (low <= close)
);

CREATE INDEX IF NOT EXISTS idx_bars_symbol_time ON market_data.bars(symbol, timestamp);
CREATE INDEX IF NOT EXISTS idx_bars_timestamp ON market_data.bars(timestamp);

-- Convert bars table to TimescaleDB hypertable
SELECT create_hypertable(
    'market_data.bars',
    'timestamp',
    chunk_time_interval => INTERVAL '1 month',
    if_not_exists => TRUE
);

-- Create corporate_actions table
CREATE TABLE IF NOT EXISTS market_data.corporate_actions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    action_type VARCHAR(20) NOT NULL,
    ex_date DATE NOT NULL,
    split_ratio DOUBLE PRECISION,
    dividend_amount DOUBLE PRECISION,
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    processed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_corp_actions_symbol_date ON market_data.corporate_actions(symbol, ex_date);
CREATE INDEX IF NOT EXISTS idx_corp_actions_type ON market_data.corporate_actions(action_type);

-- Create data_quality_log table
CREATE TABLE IF NOT EXISTS market_data.data_quality_log (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    check_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    check_time TIMESTAMP NOT NULL DEFAULT NOW(),
    date_range_start DATE,
    date_range_end DATE,
    issue_count INTEGER DEFAULT 0,
    details TEXT,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dq_log_symbol_check_time ON market_data.data_quality_log(symbol, check_type, check_time);
CREATE INDEX IF NOT EXISTS idx_dq_log_check_time ON market_data.data_quality_log(check_time);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA market_data TO aiinvest;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA market_data TO aiinvest;
