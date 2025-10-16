# M1 Data Hub - Quick Start Guide

This guide helps you get started with the M1 Data Hub implementation for automated EOD equity data ingestion.

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ installed
- Make installed (optional, for convenience)

## 1. Start the Infrastructure

Start PostgreSQL (with TimescaleDB) and Redis:

```bash
cd /home/runner/work/ai-investing-tool/ai-investing-tool
docker compose up -d postgres redis
```

Wait for services to be healthy (check with `docker compose ps`).

## 2. Run Database Migration

Create the market data schema and tables:

```bash
# Using Docker to run SQL migration
docker exec -i aiinvest-postgres psql -U aiinvest -d aiinvest < apps/workers/migration.sql
```

Verify the hypertable was created:

```bash
docker exec aiinvest-postgres psql -U aiinvest -d aiinvest -c \
  "SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name='bars';"
```

You should see output indicating the `bars` table is now a TimescaleDB hypertable.

## 3. Install Python Dependencies

```bash
# Create virtual environment
cd apps/workers
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Note:** If you encounter network issues with pip, you can install packages individually or use a requirements mirror.

## 4. Seed Demo Data

Populate the database with sample symbols and historical data:

```bash
# From the repository root
cd /home/runner/work/ai-investing-tool/ai-investing-tool
python scripts/seed_demo.py
```

This will:
- Add 5 demo symbols (SPY, AAPL, MSFT, GOOGL, AMZN)
- Fetch 2 years of historical EOD data from yfinance
- Store corporate actions (splits and dividends)
- Run initial data quality checks

Expected output:
```
2025-10-15 22:00:00 - INFO - Seeding symbols...
2025-10-15 22:00:01 - INFO - Added symbol: SPY
2025-10-15 22:00:01 - INFO - Added symbol: AAPL
...
2025-10-15 22:00:10 - INFO - Seeding 2 years of historical data...
2025-10-15 22:00:15 - INFO - Stored 504 bars for SPY
...
```

## 5. Verify Data Was Loaded

Check the database:

```bash
# Count symbols
docker exec aiinvest-postgres psql -U aiinvest -d aiinvest -c \
  "SELECT COUNT(*) FROM market_data.symbol_map;"

# View symbols
docker exec aiinvest-postgres psql -U aiinvest -d aiinvest -c \
  "SELECT symbol, name, asset_type FROM market_data.symbol_map;"

# Count bars
docker exec aiinvest-postgres psql -U aiinvest -d aiinvest -c \
  "SELECT symbol, COUNT(*) as bar_count FROM market_data.bars GROUP BY symbol;"

# Sample data
docker exec aiinvest-postgres psql -U aiinvest -d aiinvest -c \
  "SELECT symbol, timestamp, close FROM market_data.bars ORDER BY timestamp DESC LIMIT 10;"
```

## 6. Manual Operations with CLI

Use the CLI tool for manual operations:

```bash
# List all symbols
python scripts/data_hub_cli.py list-symbols

# Add a new symbol
python scripts/data_hub_cli.py add-symbol TSLA --name "Tesla Inc." --exchange NASDAQ

# Ingest recent data for a symbol
python scripts/data_hub_cli.py ingest TSLA --start-date 2024-01-01

# Repair missing data
python scripts/data_hub_cli.py repair SPY --lookback-days 30

# Run QA checks
python scripts/data_hub_cli.py qa-check SPY

# View recent QA issues
python scripts/data_hub_cli.py view-issues --severity warning --days 7
```

## 7. Start the Scheduler (Optional)

Start the automated scheduler for daily data ingestion:

```bash
cd apps/workers
python scheduler.py
```

The scheduler runs these jobs daily:
- **6 PM ET**: EOD data ingestion for all active symbols
- **7 PM ET**: Missing data repair
- **8 PM ET**: Corporate actions ingestion
- **9 PM ET**: Data quality checks

Press `Ctrl+C` to stop the scheduler.

To run jobs immediately on startup (for testing):
```bash
RUN_JOBS_ON_STARTUP=true python scheduler.py
```

## 8. Using Docker Compose (Alternative)

You can also run the workers as a Docker service:

```bash
# Uncomment the command in docker-compose.yml for data-hub-workers service
# Then run:
docker compose up -d data-hub-workers

# View logs
docker compose logs -f data-hub-workers
```

## Database Schema

### symbol_map
Stores ticker metadata and tracking status.

### bars (Hypertable)
Stores OHLCV data, partitioned by time (1-month chunks).

### corporate_actions
Tracks splits and dividends.

### data_quality_log
Logs QA check results and issues.

## Data Quality Checks

The system automatically runs three types of checks:

1. **Duplicate Detection**: Identifies duplicate bars
2. **Completeness**: Verifies sufficient data per time period
3. **Anomaly Detection**: Detects price spikes and volume outliers

View recent issues:
```bash
python scripts/data_hub_cli.py view-issues
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check logs
docker compose logs postgres

# Test connection manually
psql postgresql://aiinvest:pass@localhost:5432/aiinvest -c "SELECT version();"
```

### Missing Data

```bash
# Run repair for specific symbol
python scripts/data_hub_cli.py repair SPY --lookback-days 90

# Check for issues
python scripts/data_hub_cli.py view-issues --symbol SPY
```

### Scheduler Not Running

```bash
# Check if the script is executable
ls -la apps/workers/scheduler.py

# Run with explicit python
python apps/workers/scheduler.py

# Check for Python errors
python -c "from apps.workers.scheduler import DataHubScheduler; print('OK')"
```

## Next Steps

1. **Add More Symbols**: Use the CLI to add more symbols to track
2. **Configure Schedule**: Adjust cron schedules in `scheduler.py` for your timezone
3. **Monitor Data Quality**: Regularly check QA logs for issues
4. **Integrate with Backtester**: Use the market data for backtesting strategies
5. **Set Up Alerts**: Configure notifications for data quality issues

## Environment Variables

Key environment variables (in `.env`):

```bash
POSTGRES_URL=postgresql://aiinvest:pass@localhost:5432/aiinvest
REDIS_URL=redis://localhost:6379/0
RUN_JOBS_ON_STARTUP=false
LOG_LEVEL=INFO
DB_POOL_SIZE=20
```

## API Usage (Programmatic)

```python
from apps.workers.ingestion import DataIngestionService
from apps.workers.data_quality import DataQualityService
from datetime import datetime, timedelta

# Initialize services
ingestion = DataIngestionService()
qa = DataQualityService()

# Add and ingest data for a symbol
ingestion.add_symbol('NVDA', name='NVIDIA Corporation')
count = ingestion.ingest_symbol_data(
    'NVDA',
    start_date=datetime.now().date() - timedelta(days=365),
    end_date=datetime.now().date()
)
print(f"Ingested {count} bars for NVDA")

# Run QA checks
results = qa.run_all_checks(
    'NVDA',
    datetime.now().date() - timedelta(days=30),
    datetime.now().date()
)
for result in results:
    print(f"{result['check_type']}: {result['issue_count']} issues")
```

## Performance Tips

1. **Batch Operations**: Ingest multiple symbols at once using the scheduler
2. **Optimize Queries**: Use time-based indexes for efficient lookups
3. **Connection Pooling**: Adjust `DB_POOL_SIZE` based on your workload
4. **Compression**: Enable TimescaleDB compression for older data
5. **Retention**: Set up data retention policies for very old data

## Support

For issues or questions:
1. Check the logs: `docker compose logs postgres` or `docker compose logs data-hub-workers`
2. Review the comprehensive README: `apps/workers/README.md`
3. Check QA logs: `python scripts/data_hub_cli.py view-issues`

---

**Congratulations!** Your M1 Data Hub is now set up and ready to ingest EOD equity data automatically.
