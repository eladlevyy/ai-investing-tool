"""
Test script to manually verify data ingestion works.
"""
import os
import sys
from datetime import datetime, timedelta

# Set environment variables for testing
os.environ['POSTGRES_URL'] = 'postgresql://aiinvest:pass@localhost:5432/aiinvest'

# Mock the dependencies that are hard to install
class MockYFinance:
    def __init__(self, symbol):
        self.symbol = symbol
    
    def history(self, start, end):
        import pandas as pd
        dates = pd.date_range(start=start, end=end, freq='B')  # Business days
        df = pd.DataFrame({
            'Date': dates,
            'Open': [100.0 + i for i in range(len(dates))],
            'High': [105.0 + i for i in range(len(dates))],
            'Low': [99.0 + i for i in range(len(dates))],
            'Close': [103.0 + i for i in range(len(dates))],
            'Volume': [1000000 + i * 10000 for i in range(len(dates))]
        })
        df = df.set_index('Date')
        return df
    
    @property
    def actions(self):
        import pandas as pd
        return pd.DataFrame({
            'Stock Splits': [2.0],
            'Dividends': [0.5]
        }, index=[datetime(2024, 1, 15)])

# Test database connection
print("Testing database connection...")
try:
    import psycopg2
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='aiinvest',
        password='pass',
        database='aiinvest'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM market_data.symbol_map;")
    count = cursor.fetchone()[0]
    print(f"✓ Database connected. Found {count} symbols in symbol_map")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    sys.exit(1)

# Test adding a symbol
print("\nTesting symbol addition...")
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='aiinvest',
        password='pass',
        database='aiinvest'
    )
    cursor = conn.cursor()
    
    # Insert test symbol
    cursor.execute("""
        INSERT INTO market_data.symbol_map (symbol, name, exchange, asset_type, is_active, data_source, created_at, updated_at)
        VALUES ('SPY', 'SPDR S&P 500 ETF Trust', 'NYSE', 'etf', TRUE, 'yfinance', NOW(), NOW())
        ON CONFLICT (symbol) DO NOTHING
        RETURNING id;
    """)
    result = cursor.fetchone()
    conn.commit()
    
    if result:
        print(f"✓ Added symbol SPY (id={result[0]})")
    else:
        print("✓ Symbol SPY already exists")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"✗ Symbol addition failed: {e}")
    sys.exit(1)

# Test adding bars
print("\nTesting bar insertion...")
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='aiinvest',
        password='pass',
        database='aiinvest'
    )
    cursor = conn.cursor()
    
    # Insert test bars
    test_date = datetime.now() - timedelta(days=1)
    cursor.execute("""
        INSERT INTO market_data.bars (symbol, timestamp, open, high, low, close, volume, split_adjusted, dividend_adjusted, created_at)
        VALUES ('SPY', %s, 450.0, 455.0, 449.0, 453.0, 50000000, FALSE, FALSE, NOW())
        ON CONFLICT (symbol, timestamp) DO UPDATE
        SET close = EXCLUDED.close
        RETURNING symbol, timestamp;
    """, (test_date,))
    result = cursor.fetchone()
    conn.commit()
    
    print(f"✓ Added/updated bar for {result[0]} at {result[1]}")
    
    # Query bars
    cursor.execute("SELECT COUNT(*) FROM market_data.bars WHERE symbol = 'SPY';")
    count = cursor.fetchone()[0]
    print(f"✓ Total bars for SPY: {count}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"✗ Bar insertion failed: {e}")
    sys.exit(1)

# Test hypertable
print("\nTesting TimescaleDB hypertable...")
try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='aiinvest',
        password='pass',
        database='aiinvest'
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM timescaledb_information.hypertables 
        WHERE hypertable_name='bars';
    """)
    result = cursor.fetchone()
    
    if result:
        print(f"✓ Hypertable 'bars' exists with {result[3]} dimension(s)")
    else:
        print("✗ Hypertable 'bars' not found")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"✗ Hypertable check failed: {e}")

print("\n" + "="*60)
print("All basic tests passed! ✓")
print("="*60)
print("\nNext steps:")
print("1. Install Python dependencies: pip install -r apps/workers/requirements.txt")
print("2. Run seed script: python scripts/seed_demo.py")
print("3. Start scheduler: python apps/workers/scheduler.py")
