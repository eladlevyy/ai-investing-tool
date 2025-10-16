# Data Hub - M1 Implementation

The Data Hub provides automated EOD (End-of-Day) equities data ingestion, quality checks, and maintenance for the AI Investing Tool.

## Features

### 1. **EOD Data Ingestion**
- Automated daily ingestion of equity data from yfinance
- Support for multiple symbols (SPY, AAPL, MSFT, GOOGL, AMZN, etc.)
- Historical data backfill capability
- Upsert logic to handle duplicate prevention

### 2. **Late Repair Mechanism**
- Automatically detects missing bars (gaps in data)
- Scheduled repair jobs to fill missing data
- Configurable lookback period

### 3. **Symbol Management**
- Symbol map table for ticker metadata
- Track active/inactive symbols
- Support for equities and ETFs
- Metadata: name, exchange, sector, industry

### 4. **Corporate Actions Pipeline**
- Ingestion of stock splits and dividends
- Historical corporate actions tracking
- Ready for future price adjustment implementation

### 5. **TimescaleDB Hypertables**
- Bars table converted to TimescaleDB hypertable
- Automatic time-based partitioning (1-month chunks)
- Optimized indexes for time-series queries
- Efficient storage and query performance

### 6. **Data Quality Checks**
- **Duplicate Detection**: Identifies duplicate bars
- **Completeness Checks**: Verifies sufficient data per time period
- **Anomaly Detection**: Detects price spikes and volume outliers
- All checks logged to data_quality_log table

### 7. **Automated Scheduler**
- Daily EOD ingestion at 6 PM ET
- Missing data repair at 7 PM ET
- Corporate actions ingestion at 8 PM ET
- Data quality checks at 9 PM ET

## Architecture

```
apps/workers/
├── db.py                  # Database connection and session management
├── models.py              # SQLAlchemy models (SymbolMap, Bar, CorporateAction, DataQualityLog)
├── ingestion.py           # Data ingestion service
├── data_quality.py        # Data quality checks service
├── scheduler.py           # Automated scheduler
├── requirements.txt       # Python dependencies
├── alembic.ini           # Alembic configuration
└── alembic/              # Database migrations
    ├── env.py
    └── versions/
        └── 001_init_market_data.py

scripts/
├── seed_demo.py          # Database seeding script
└── data_hub_cli.py       # CLI tool for manual operations
```

## Database Schema

### market_data.symbol_map
- Stores ticker metadata
- Fields: id, symbol, name, exchange, asset_type, sector, industry, is_active, data_source, created_at, updated_at
- Indexes: symbol (unique)

### market_data.bars (Hypertable)
- Stores OHLCV bar data
- Fields: id, symbol, timestamp, open, high, low, close, volume, adjusted_close, split_adjusted, dividend_adjusted, created_at
- Partitioned by: timestamp (1-month chunks)
- Indexes: (symbol, timestamp), timestamp
- Constraints: Price and volume validation checks

### market_data.corporate_actions
- Stores splits and dividends
- Fields: id, symbol, action_type, ex_date, split_ratio, dividend_amount, processed, processed_at, created_at
- Indexes: (symbol, ex_date), action_type

### market_data.data_quality_log
- Stores QA check results
- Fields: id, symbol, check_type, severity, check_time, date_range_start, date_range_end, issue_count, details, resolved, resolved_at
- Indexes: (symbol, check_type, check_time), check_time

## Setup

### 1. Start Infrastructure
```bash
# Start PostgreSQL with TimescaleDB, Redis, MinIO
docker compose up -d

# Wait for services to be healthy
docker compose ps
```

### 2. Run Database Migration
```bash
cd apps/workers
python -m pip install -r requirements.txt
alembic upgrade head
```

### 3. Seed Demo Data
```bash
# Seed symbols and 2 years of historical data
python scripts/seed_demo.py
```

## Usage

### Automated Scheduler
```bash
# Start the scheduler (runs in foreground)
cd apps/workers
python scheduler.py

# Or with jobs running immediately on startup
RUN_JOBS_ON_STARTUP=true python scheduler.py
```

### Manual CLI Operations

```bash
# Add a new symbol
python scripts/data_hub_cli.py add-symbol TSLA --name "Tesla Inc." --exchange NASDAQ --sector Technology

# Ingest data for a symbol
python scripts/data_hub_cli.py ingest TSLA --start-date 2023-01-01

# Repair missing data
python scripts/data_hub_cli.py repair TSLA --lookback-days 30

# Ingest corporate actions
python scripts/data_hub_cli.py corporate-actions AAPL

# Run QA checks
python scripts/data_hub_cli.py qa-check SPY

# List all symbols
python scripts/data_hub_cli.py list-symbols

# View recent QA issues
python scripts/data_hub_cli.py view-issues --severity error --days 7
```

### Programmatic Usage

```python
from apps.workers.ingestion import DataIngestionService
from apps.workers.data_quality import DataQualityService

# Ingest data
service = DataIngestionService()
service.add_symbol('TSLA', name='Tesla Inc.')
count = service.ingest_symbol_data('TSLA', start_date, end_date)

# Run QA checks
qa_service = DataQualityService()
results = qa_service.run_all_checks('TSLA', start_date, end_date)
```

## Configuration

### Environment Variables
```bash
# Database
POSTGRES_URL=postgresql://aiinvest:pass@localhost:5432/aiinvest

# Scheduler
RUN_JOBS_ON_STARTUP=false  # Set to true to run jobs immediately on startup

# Connection Pool
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30

# Logging
DEBUG=false
LOG_LEVEL=INFO
```

## Scheduled Jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| Daily EOD Ingestion | 6 PM ET | Fetch latest EOD data for all active symbols |
| Missing Data Repair | 7 PM ET | Identify and repair missing bars |
| Corporate Actions | 8 PM ET | Fetch splits and dividends |
| Data Quality Checks | 9 PM ET | Run duplicate, completeness, and anomaly checks |

## Data Quality Checks

### 1. Duplicate Detection
- Identifies bars with duplicate (symbol, timestamp) pairs
- Severity: ERROR if duplicates found

### 2. Completeness Checks
- Verifies minimum bars per month (default: 20)
- Accounts for weekends and market holidays
- Severity: WARNING if incomplete

### 3. Anomaly Detection
- **Price Spikes**: Returns > 5 standard deviations
- **Volume Spikes**: Volume > 10 standard deviations
- Uses z-score for detection
- Severity: WARNING if anomalies found

## Performance Optimizations

1. **TimescaleDB Hypertables**: Time-based partitioning for efficient queries
2. **Indexes**: Optimized for time-series lookback queries
3. **Connection Pooling**: Reuses database connections
4. **Batch Upserts**: Efficient bulk inserts with conflict resolution
5. **Pre-ping**: Health checks on connections before use

## Future Enhancements

- [ ] Apply corporate action adjustments to historical bars
- [ ] Support for intraday data (minute bars)
- [ ] Additional data sources (Polygon, Alpha Vantage)
- [ ] Real-time data feeds
- [ ] More sophisticated anomaly detection (ML-based)
- [ ] Automatic holiday calendar integration
- [ ] Data retention policies
- [ ] Performance metrics and monitoring

## Testing

```bash
# Run unit tests (once implemented)
pytest apps/workers/tests/

# Verify database setup
docker exec -it aiinvest-postgres psql -U aiinvest -d aiinvest -c "SELECT * FROM market_data.symbol_map;"

# Check hypertable
docker exec -it aiinvest-postgres psql -U aiinvest -d aiinvest -c "SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name='bars';"
```

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Test connection
psql postgresql://aiinvest:pass@localhost:5432/aiinvest -c "SELECT version();"
```

### Missing Data
```bash
# Run repair for specific symbol
python scripts/data_hub_cli.py repair SPY --lookback-days 90

# Check QA logs for issues
python scripts/data_hub_cli.py view-issues --symbol SPY
```

### Scheduler Not Running
```bash
# Check logs
docker compose logs -f

# Run jobs manually via CLI instead
python scripts/data_hub_cli.py ingest SPY
```

## License

See main repository LICENSE file.
