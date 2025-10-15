"""
Scheduler for automated EOD data ingestion and maintenance tasks.
"""
import logging
from datetime import datetime, date, timedelta
import os

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from ingestion import DataIngestionService
from data_quality import DataQualityService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataHubScheduler:
    """
    Scheduler for automated data ingestion and quality checks.
    """
    
    def __init__(self):
        self.scheduler = BlockingScheduler()
        self.ingestion_service = DataIngestionService()
        self.qa_service = DataQualityService()
        self.logger = logging.getLogger(__name__)
    
    def ingest_all_symbols(self) -> None:
        """
        Ingest EOD data for all active symbols.
        Called daily after market close.
        """
        self.logger.info("Starting daily EOD data ingestion")
        
        try:
            symbols = self.ingestion_service.fetch_symbols(active_only=True)
            
            if not symbols:
                self.logger.warning("No active symbols found in symbol_map")
                return
            
            self.logger.info(f"Ingesting data for {len(symbols)} symbols")
            
            # Fetch data for last 5 days to ensure we catch any missed days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=5)
            
            success_count = 0
            error_count = 0
            
            for symbol in symbols:
                try:
                    count = self.ingestion_service.ingest_symbol_data(
                        symbol,
                        start_date,
                        end_date
                    )
                    if count > 0:
                        success_count += 1
                        self.logger.info(f"Ingested {count} bars for {symbol}")
                    else:
                        self.logger.warning(f"No new data for {symbol}")
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"Error ingesting {symbol}: {str(e)}")
            
            self.logger.info(
                f"Daily ingestion complete: {success_count} successful, {error_count} errors"
            )
            
        except Exception as e:
            self.logger.error(f"Error in daily ingestion: {str(e)}")
    
    def repair_missing_data(self) -> None:
        """
        Repair missing bars for all symbols.
        Called daily to fill any gaps in data.
        """
        self.logger.info("Starting missing data repair")
        
        try:
            symbols = self.ingestion_service.fetch_symbols(active_only=True)
            
            if not symbols:
                self.logger.warning("No active symbols found")
                return
            
            total_repaired = 0
            
            for symbol in symbols:
                try:
                    # Look back 30 days for missing bars
                    repaired = self.ingestion_service.repair_missing_bars(
                        symbol,
                        lookback_days=30
                    )
                    total_repaired += repaired
                    
                    if repaired > 0:
                        self.logger.info(f"Repaired {repaired} bars for {symbol}")
                        
                except Exception as e:
                    self.logger.error(f"Error repairing {symbol}: {str(e)}")
            
            self.logger.info(f"Missing data repair complete: {total_repaired} bars repaired")
            
        except Exception as e:
            self.logger.error(f"Error in missing data repair: {str(e)}")
    
    def ingest_corporate_actions(self) -> None:
        """
        Ingest corporate actions for all symbols.
        Called daily to fetch new splits and dividends.
        """
        self.logger.info("Starting corporate actions ingestion")
        
        try:
            symbols = self.ingestion_service.fetch_symbols(active_only=True)
            
            if not symbols:
                self.logger.warning("No active symbols found")
                return
            
            # Fetch actions for last 7 days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=7)
            
            total_actions = 0
            
            for symbol in symbols:
                try:
                    count = self.ingestion_service.ingest_corporate_actions(
                        symbol,
                        start_date,
                        end_date
                    )
                    total_actions += count
                    
                    if count > 0:
                        self.logger.info(f"Ingested {count} corporate actions for {symbol}")
                        
                except Exception as e:
                    self.logger.error(f"Error ingesting corporate actions for {symbol}: {str(e)}")
            
            self.logger.info(f"Corporate actions ingestion complete: {total_actions} actions")
            
        except Exception as e:
            self.logger.error(f"Error in corporate actions ingestion: {str(e)}")
    
    def run_quality_checks(self) -> None:
        """
        Run data quality checks for all symbols.
        Called daily to detect anomalies and issues.
        """
        self.logger.info("Starting data quality checks")
        
        try:
            symbols = self.ingestion_service.fetch_symbols(active_only=True)
            
            if not symbols:
                self.logger.warning("No active symbols found")
                return
            
            # Check data for last 30 days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            for symbol in symbols:
                try:
                    results = self.qa_service.run_all_checks(symbol, start_date, end_date)
                    
                    # Log any issues found
                    for result in results:
                        if result['issue_count'] > 0:
                            self.logger.warning(
                                f"{symbol}: {result['check_type']} - "
                                f"{result['issue_count']} issues ({result['severity']})"
                            )
                            
                except Exception as e:
                    self.logger.error(f"Error checking {symbol}: {str(e)}")
            
            self.logger.info("Data quality checks complete")
            
        except Exception as e:
            self.logger.error(f"Error in quality checks: {str(e)}")
    
    def setup_jobs(self) -> None:
        """
        Set up scheduled jobs.
        """
        # Daily EOD data ingestion - runs at 6 PM ET (after market close)
        # In production, adjust timezone as needed
        self.scheduler.add_job(
            self.ingest_all_symbols,
            CronTrigger(hour=18, minute=0),
            id='daily_eod_ingestion',
            name='Daily EOD Data Ingestion',
            replace_existing=True
        )
        
        # Missing data repair - runs at 7 PM ET
        self.scheduler.add_job(
            self.repair_missing_data,
            CronTrigger(hour=19, minute=0),
            id='daily_repair',
            name='Daily Missing Data Repair',
            replace_existing=True
        )
        
        # Corporate actions ingestion - runs at 8 PM ET
        self.scheduler.add_job(
            self.ingest_corporate_actions,
            CronTrigger(hour=20, minute=0),
            id='daily_corporate_actions',
            name='Daily Corporate Actions Ingestion',
            replace_existing=True
        )
        
        # Data quality checks - runs at 9 PM ET
        self.scheduler.add_job(
            self.run_quality_checks,
            CronTrigger(hour=21, minute=0),
            id='daily_qa_checks',
            name='Daily Data Quality Checks',
            replace_existing=True
        )
        
        self.logger.info("Scheduled jobs configured:")
        for job in self.scheduler.get_jobs():
            self.logger.info(f"  - {job.name} ({job.id}): {job.trigger}")
    
    def start(self) -> None:
        """
        Start the scheduler.
        """
        self.logger.info("Starting Data Hub Scheduler")
        self.setup_jobs()
        
        # Run jobs once at startup for testing/initialization
        run_on_startup = os.getenv("RUN_JOBS_ON_STARTUP", "false").lower() == "true"
        if run_on_startup:
            self.logger.info("Running all jobs once at startup")
            self.ingest_all_symbols()
            self.repair_missing_data()
            self.ingest_corporate_actions()
            self.run_quality_checks()
        
        # Start the scheduler
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.logger.info("Scheduler stopped")


if __name__ == "__main__":
    scheduler = DataHubScheduler()
    scheduler.start()
