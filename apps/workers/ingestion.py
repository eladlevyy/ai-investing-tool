"""
Data ingestion service for fetching EOD equity data from yfinance.
Includes late repair for missing bars and data quality checks.
"""
import logging
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
import json

import yfinance as yf
import pandas as pd
from sqlalchemy import and_, func, text
from sqlalchemy.dialects.postgresql import insert

from db import get_db
from models import Bar, SymbolMap, CorporateAction, DataQualityLog

logger = logging.getLogger(__name__)


class DataIngestionService:
    """
    Service for ingesting EOD equity data and managing data quality.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def fetch_symbols(self, active_only: bool = True) -> List[str]:
        """
        Fetch list of symbols from symbol_map table.
        
        Args:
            active_only: If True, only return active symbols
            
        Returns:
            List of symbol strings
        """
        with get_db() as db:
            query = db.query(SymbolMap.symbol)
            if active_only:
                query = query.filter(SymbolMap.is_active == True)
            symbols = [row[0] for row in query.all()]
        return symbols
    
    def add_symbol(
        self,
        symbol: str,
        name: Optional[str] = None,
        exchange: Optional[str] = None,
        asset_type: str = 'equity',
        sector: Optional[str] = None,
        industry: Optional[str] = None,
        data_source: str = 'yfinance'
    ) -> bool:
        """
        Add a new symbol to the symbol_map table.
        
        Args:
            symbol: Ticker symbol
            name: Company/asset name
            exchange: Exchange where traded
            asset_type: Type of asset (equity, etf, etc.)
            sector: Sector classification
            industry: Industry classification
            data_source: Data source identifier
            
        Returns:
            True if added successfully, False if already exists
        """
        with get_db() as db:
            existing = db.query(SymbolMap).filter(SymbolMap.symbol == symbol).first()
            if existing:
                self.logger.warning(f"Symbol {symbol} already exists in symbol_map")
                return False
            
            symbol_map = SymbolMap(
                symbol=symbol,
                name=name,
                exchange=exchange,
                asset_type=asset_type,
                sector=sector,
                industry=industry,
                is_active=True,
                data_source=data_source,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(symbol_map)
            db.commit()
            self.logger.info(f"Added symbol {symbol} to symbol_map")
            return True
    
    def fetch_eod_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Fetch EOD data from yfinance for a given symbol.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date for data fetch (defaults to 1 year ago)
            end_date: End date for data fetch (defaults to today)
            
        Returns:
            DataFrame with OHLCV data
        """
        if start_date is None:
            start_date = datetime.now().date() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now().date()
        
        self.logger.info(f"Fetching data for {symbol} from {start_date} to {end_date}")
        
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                self.logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            # Reset index to get date as a column
            df = df.reset_index()
            
            # Rename columns to match our schema
            df = df.rename(columns={
                'Date': 'timestamp',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # Add symbol column
            df['symbol'] = symbol
            
            # Keep only columns we need
            columns = ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
            df = df[columns]
            
            # Remove any rows with NaN values
            df = df.dropna()
            
            self.logger.info(f"Fetched {len(df)} bars for {symbol}")
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def store_bars(self, df: pd.DataFrame) -> int:
        """
        Store bars in the database using upsert (insert or update on conflict).
        
        Args:
            df: DataFrame with bar data
            
        Returns:
            Number of bars stored
        """
        if df.empty:
            return 0
        
        with get_db() as db:
            # Prepare data for insertion
            records = df.to_dict('records')
            for record in records:
                record['split_adjusted'] = False
                record['dividend_adjusted'] = False
                record['created_at'] = datetime.utcnow()
            
            # Use PostgreSQL UPSERT (ON CONFLICT DO UPDATE)
            stmt = insert(Bar).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=['symbol', 'timestamp'],
                set_={
                    'open': stmt.excluded.open,
                    'high': stmt.excluded.high,
                    'low': stmt.excluded.low,
                    'close': stmt.excluded.close,
                    'volume': stmt.excluded.volume,
                }
            )
            
            db.execute(stmt)
            db.commit()
            
            self.logger.info(f"Stored {len(records)} bars")
            return len(records)
    
    def ingest_symbol_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> int:
        """
        Complete ingestion workflow for a symbol: fetch and store data.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date for data fetch
            end_date: End date for data fetch
            
        Returns:
            Number of bars stored
        """
        df = self.fetch_eod_data(symbol, start_date, end_date)
        if df.empty:
            return 0
        return self.store_bars(df)
    
    def find_missing_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> List[date]:
        """
        Identify missing trading days for a symbol.
        Compares expected trading days (Mon-Fri, excluding holidays) with actual data.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date to check
            end_date: End date to check
            
        Returns:
            List of dates with missing data
        """
        with get_db() as db:
            # Get all dates we have data for
            result = db.query(func.date(Bar.timestamp)).filter(
                and_(
                    Bar.symbol == symbol,
                    func.date(Bar.timestamp) >= start_date,
                    func.date(Bar.timestamp) <= end_date
                )
            ).distinct().all()
            
            existing_dates = set(row[0] for row in result)
        
        # Generate expected trading days (approximate - Mon-Fri)
        expected_dates = set()
        current = start_date
        while current <= end_date:
            # Skip weekends (0=Monday, 6=Sunday)
            if current.weekday() < 5:
                expected_dates.add(current)
            current += timedelta(days=1)
        
        # Find missing dates
        missing_dates = sorted(expected_dates - existing_dates)
        
        if missing_dates:
            self.logger.info(f"Found {len(missing_dates)} missing dates for {symbol}")
        
        return missing_dates
    
    def repair_missing_bars(
        self,
        symbol: str,
        lookback_days: int = 30
    ) -> int:
        """
        Repair missing bars by re-fetching data for identified gaps.
        
        Args:
            symbol: Ticker symbol
            lookback_days: Number of days to look back for missing data
            
        Returns:
            Number of bars repaired
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=lookback_days)
        
        missing_dates = self.find_missing_bars(symbol, start_date, end_date)
        
        if not missing_dates:
            self.logger.info(f"No missing bars found for {symbol}")
            return 0
        
        # Fetch data for the entire range to fill gaps
        # This is more efficient than fetching individual days
        df = self.fetch_eod_data(symbol, start_date, end_date)
        if df.empty:
            return 0
        
        # Filter to only missing dates
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        df = df[df['date'].isin(missing_dates)]
        df = df.drop('date', axis=1)
        
        if df.empty:
            self.logger.warning(f"Could not fetch data for missing dates for {symbol}")
            return 0
        
        repaired_count = self.store_bars(df)
        self.logger.info(f"Repaired {repaired_count} missing bars for {symbol}")
        
        return repaired_count
    
    def fetch_corporate_actions(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Fetch splits and dividends from yfinance.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date for fetching actions
            end_date: End date for fetching actions
            
        Returns:
            Dictionary with 'splits' and 'dividends' DataFrames
        """
        if start_date is None:
            start_date = datetime.now().date() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now().date()
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Get actions (splits and dividends)
            actions = ticker.actions
            if actions is None or actions.empty:
                return {'splits': pd.DataFrame(), 'dividends': pd.DataFrame()}
            
            # Filter by date range
            actions = actions.loc[start_date:end_date]
            
            # Separate splits and dividends
            splits = actions[actions['Stock Splits'] > 0]['Stock Splits']
            dividends = actions[actions['Dividends'] > 0]['Dividends']
            
            self.logger.info(f"Found {len(splits)} splits and {len(dividends)} dividends for {symbol}")
            
            return {
                'splits': splits.reset_index(),
                'dividends': dividends.reset_index()
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching corporate actions for {symbol}: {str(e)}")
            return {'splits': pd.DataFrame(), 'dividends': pd.DataFrame()}
    
    def store_corporate_actions(
        self,
        symbol: str,
        splits: pd.DataFrame,
        dividends: pd.DataFrame
    ) -> int:
        """
        Store corporate actions in the database.
        
        Args:
            symbol: Ticker symbol
            splits: DataFrame with split data
            dividends: DataFrame with dividend data
            
        Returns:
            Number of actions stored
        """
        count = 0
        
        with get_db() as db:
            # Store splits
            for _, row in splits.iterrows():
                ex_date = row['Date'].date() if isinstance(row['Date'], pd.Timestamp) else row['Date']
                
                # Check if already exists
                existing = db.query(CorporateAction).filter(
                    and_(
                        CorporateAction.symbol == symbol,
                        CorporateAction.action_type == 'split',
                        CorporateAction.ex_date == ex_date
                    )
                ).first()
                
                if not existing:
                    action = CorporateAction(
                        symbol=symbol,
                        action_type='split',
                        ex_date=ex_date,
                        split_ratio=float(row['Stock Splits']),
                        processed=False,
                        created_at=datetime.utcnow()
                    )
                    db.add(action)
                    count += 1
            
            # Store dividends
            for _, row in dividends.iterrows():
                ex_date = row['Date'].date() if isinstance(row['Date'], pd.Timestamp) else row['Date']
                
                # Check if already exists
                existing = db.query(CorporateAction).filter(
                    and_(
                        CorporateAction.symbol == symbol,
                        CorporateAction.action_type == 'dividend',
                        CorporateAction.ex_date == ex_date
                    )
                ).first()
                
                if not existing:
                    action = CorporateAction(
                        symbol=symbol,
                        action_type='dividend',
                        ex_date=ex_date,
                        dividend_amount=float(row['Dividends']),
                        processed=False,
                        created_at=datetime.utcnow()
                    )
                    db.add(action)
                    count += 1
            
            db.commit()
        
        self.logger.info(f"Stored {count} corporate actions for {symbol}")
        return count
    
    def ingest_corporate_actions(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> int:
        """
        Complete workflow for ingesting corporate actions.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date for fetching actions
            end_date: End date for fetching actions
            
        Returns:
            Number of actions stored
        """
        actions = self.fetch_corporate_actions(symbol, start_date, end_date)
        return self.store_corporate_actions(
            symbol,
            actions['splits'],
            actions['dividends']
        )
