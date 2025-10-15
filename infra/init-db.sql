-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS market_data;
CREATE SCHEMA IF NOT EXISTS strategies;
CREATE SCHEMA IF NOT EXISTS backtests;
CREATE SCHEMA IF NOT EXISTS trades;
CREATE SCHEMA IF NOT EXISTS audit;

-- Set search path
SET search_path TO public, market_data, strategies, backtests, trades, audit;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aiinvest;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA market_data TO aiinvest;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA strategies TO aiinvest;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA backtests TO aiinvest;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA trades TO aiinvest;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA audit TO aiinvest;

-- Note: Detailed table schemas will be created via migrations
-- This file only sets up the basic database structure
