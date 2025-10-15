# readme.md

## Quick Start (Dev)
**Prereqs:** Python 3.11, Node 20, Docker, Make.

```bash
# 1) Clone & bootstrap
make bootstrap  # installs pre‑commit, sets up venv, pnpm, etc.

# 2) Bring up local stack
docker compose up -d  # Postgres+Timescale, Redis, MinIO

# 3) Run database migrations for M1 Data Hub
docker exec -i aiinvest-postgres psql -U aiinvest -d aiinvest < apps/workers/migration.sql

# 4) Seed symbols + demo bars (M1 Data Hub)
# Note: Requires Python dependencies installed
# pip install -r apps/workers/requirements.txt
python scripts/seed_demo.py

# 5) Start services (when implemented)
make api     # FastAPI on :8000
make workers # backtests & paper OMS
make web     # Next.js on :3000
```

### M1 Data Hub (Implemented ✓)
The M1 Data Hub provides automated EOD equity data ingestion:
- **EOD Data Ingestion**: Automated daily data pulls from yfinance
- **TimescaleDB Hypertables**: Efficient time-series storage with monthly partitioning
- **Late Repair**: Automatic detection and filling of missing bars
- **Corporate Actions**: Tracking of splits and dividends
- **Data Quality Checks**: Duplicate detection, completeness, and anomaly detection
- **Scheduler**: Automated daily jobs for ingestion, repair, and QA

See [QUICKSTART_M1.md](QUICKSTART_M1.md) for detailed setup instructions.

### Environment (.env)
```
POSTGRES_URL=postgresql://aiinvest:pass@localhost:5432/aiinvest
REDIS_URL=redis://localhost:6379/0
S3_ENDPOINT=http://localhost:9000
S3_BUCKET=aiinvest-artifacts
ALPACA_KEY=... (paper)
ALPACA_SECRET=...
```

### Folder Structure
```
/ai-investing-tool
  /apps
    /web (Next.js)
    /api (FastAPI)
    /workers (Celery/RQ)
  /packages
    /backtester
    /indicators
    /sdk (client)
  /infra (docker, terraform)
  /scripts
```

### Backtest Example (Python)
```python
from backtester import run_backtest, sma_cross
bt = run_backtest(
    strategy=sma_cross(short=10, long=30),
    symbols=["SPY"],
    start="2015-01-01", end="2025-01-01",
    fees={"per_share":0.005, "bps":1}, slippage_bps=5,
    seed=42,
)
print(bt.metrics)
```

### Strategy Graph Contract (simplified)
```json
{
  "nodes": [
    {"id":"universe","type":"universe","tickers":["SPY"]},
    {"id":"ind1","type":"indicator","name":"SMA","params":{"window":10}},
    {"id":"ind2","type":"indicator","name":"SMA","params":{"window":30}},
    {"id":"rule","type":"rule","expr":"cross(ind1, ind2)"},
    {"id":"size","type":"sizer","method":"vol_target","target":0.1}
  ],
  "edges": [["universe","ind1"],["universe","ind2"],["ind1","rule"],["ind2","rule"],["rule","size"]]
}
```

### Security Notes
- Store broker/API creds in KMS/Secrets Manager; never in logs.
- Sign & hash run artifacts; immutable audit trail in `audit` table.

### Legal
- This software is for **educational and research** purposes. It **does not** provide investment advice. Trading involves risk, including loss of principal.

---

## Next Steps (suggested)
1) Confirm MVP scope & pricing. 2) Generate a repo scaffold (monorepo) with working demo backtest + paper trading stub. 3) Wire broker paper keys and ship a private beta.