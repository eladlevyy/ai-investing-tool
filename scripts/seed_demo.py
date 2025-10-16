"""
Seed script to initialize the database with demo symbols and historical data.
"""
import logging
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from apps.workers.ingestion import DataIngestionService
from apps.workers.data_quality import DataQualityService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def seed_symbols():
    """
    Add initial symbols to the symbol_map table.
    """
    logger.info("Seeding symbols...")
    
    service = DataIngestionService()
    
    # Demo symbols with metadata
    symbols = [
        {
            'symbol': 'SPY',
            'name': 'SPDR S&P 500 ETF Trust',
            'exchange': 'NYSE',
            'asset_type': 'etf',
            'sector': 'Index Fund',
            'industry': 'ETF'
        },
        {
            'symbol': 'AAPL',
            'name': 'Apple Inc.',
            'exchange': 'NASDAQ',
            'asset_type': 'equity',
            'sector': 'Technology',
            'industry': 'Consumer Electronics'
        },
        {
            'symbol': 'MSFT',
            'name': 'Microsoft Corporation',
            'exchange': 'NASDAQ',
            'asset_type': 'equity',
            'sector': 'Technology',
            'industry': 'Software'
        },
        {
            'symbol': 'GOOGL',
            'name': 'Alphabet Inc.',
            'exchange': 'NASDAQ',
            'asset_type': 'equity',
            'sector': 'Technology',
            'industry': 'Internet Services'
        },
        {
            'symbol': 'AMZN',
            'name': 'Amazon.com Inc.',
            'exchange': 'NASDAQ',
            'asset_type': 'equity',
            'sector': 'Consumer Cyclical',
            'industry': 'E-commerce'
        },
    ]
    
    for symbol_data in symbols:
        try:
            added = service.add_symbol(**symbol_data)
            if added:
                logger.info(f"Added symbol: {symbol_data['symbol']}")
            else:
                logger.info(f"Symbol already exists: {symbol_data['symbol']}")
        except Exception as e:
            logger.error(f"Error adding symbol {symbol_data['symbol']}: {str(e)}")
    
    logger.info("Symbol seeding complete")


def seed_historical_data(years: int = 2):
    """
    Fetch and store historical data for all symbols.
    
    Args:
        years: Number of years of historical data to fetch
    """
    logger.info(f"Seeding {years} years of historical data...")
    
    service = DataIngestionService()
    
    # Get all active symbols
    symbols = service.fetch_symbols(active_only=True)
    
    if not symbols:
        logger.error("No symbols found in database. Run seed_symbols first.")
        return
    
    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=years * 365)
    
    logger.info(f"Fetching data from {start_date} to {end_date}")
    
    for symbol in symbols:
        try:
            logger.info(f"Fetching data for {symbol}...")
            count = service.ingest_symbol_data(symbol, start_date, end_date)
            logger.info(f"Stored {count} bars for {symbol}")
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
    
    logger.info("Historical data seeding complete")


def seed_corporate_actions():
    """
    Fetch and store corporate actions for all symbols.
    """
    logger.info("Seeding corporate actions...")
    
    service = DataIngestionService()
    
    # Get all active symbols
    symbols = service.fetch_symbols(active_only=True)
    
    if not symbols:
        logger.error("No symbols found in database.")
        return
    
    # Fetch actions for last 2 years
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=2 * 365)
    
    for symbol in symbols:
        try:
            logger.info(f"Fetching corporate actions for {symbol}...")
            count = service.ingest_corporate_actions(symbol, start_date, end_date)
            if count > 0:
                logger.info(f"Stored {count} corporate actions for {symbol}")
            else:
                logger.info(f"No corporate actions found for {symbol}")
        except Exception as e:
            logger.error(f"Error fetching corporate actions for {symbol}: {str(e)}")
    
    logger.info("Corporate actions seeding complete")


def run_initial_qa_checks():
    """
    Run initial data quality checks on seeded data.
    """
    logger.info("Running initial QA checks...")
    
    ingestion_service = DataIngestionService()
    qa_service = DataQualityService()
    
    # Get all active symbols
    symbols = ingestion_service.fetch_symbols(active_only=True)
    
    if not symbols:
        logger.error("No symbols found in database.")
        return
    
    # Check data for last 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    for symbol in symbols:
        try:
            logger.info(f"Running QA checks for {symbol}...")
            results = qa_service.run_all_checks(symbol, start_date, end_date)
            
            # Log summary
            for result in results:
                if result['issue_count'] > 0:
                    logger.warning(
                        f"{symbol}: {result['check_type']} - "
                        f"{result['issue_count']} issues ({result['severity']})"
                    )
                else:
                    logger.info(f"{symbol}: {result['check_type']} - OK")
                    
        except Exception as e:
            logger.error(f"Error running QA checks for {symbol}: {str(e)}")
    
    logger.info("Initial QA checks complete")


def main():
    """
    Main seeding workflow.
    """
    logger.info("=" * 60)
    logger.info("Starting database seeding process")
    logger.info("=" * 60)
    
    try:
        # Step 1: Seed symbols
        seed_symbols()
        
        # Step 2: Seed historical data
        seed_historical_data(years=2)
        
        # Step 3: Seed corporate actions
        seed_corporate_actions()
        
        # Step 4: Run QA checks
        run_initial_qa_checks()
        
        logger.info("=" * 60)
        logger.info("Database seeding completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error during seeding: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
