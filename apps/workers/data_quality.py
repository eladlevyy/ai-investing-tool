"""
Data Quality service for checking anomalies, duplicates, and completeness.
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Tuple
import json

import pandas as pd
import numpy as np
from sqlalchemy import and_, func

from db import get_db
from models import Bar, DataQualityLog

logger = logging.getLogger(__name__)


class DataQualityService:
    """
    Service for performing data quality checks on market data.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_duplicates(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Check for duplicate bars (same symbol and timestamp).
        
        Args:
            symbol: Ticker symbol
            start_date: Start date to check
            end_date: End date to check
            
        Returns:
            Dict with duplicate check results
        """
        with get_db() as db:
            # Query for duplicate timestamps
            duplicates = db.query(
                Bar.symbol,
                Bar.timestamp,
                func.count(Bar.id).label('count')
            ).filter(
                and_(
                    Bar.symbol == symbol,
                    func.date(Bar.timestamp) >= start_date,
                    func.date(Bar.timestamp) <= end_date
                )
            ).group_by(
                Bar.symbol, Bar.timestamp
            ).having(
                func.count(Bar.id) > 1
            ).all()
            
            duplicate_count = len(duplicates)
            
            result = {
                'symbol': symbol,
                'check_type': 'duplicate',
                'date_range_start': start_date,
                'date_range_end': end_date,
                'issue_count': duplicate_count,
                'severity': 'error' if duplicate_count > 0 else 'info',
                'details': json.dumps([
                    {
                        'timestamp': str(dup.timestamp),
                        'count': dup.count
                    }
                    for dup in duplicates[:100]  # Limit to first 100
                ]) if duplicates else None
            }
            
            if duplicate_count > 0:
                self.logger.warning(f"Found {duplicate_count} duplicate bars for {symbol}")
            else:
                self.logger.info(f"No duplicates found for {symbol}")
            
            return result
    
    def check_completeness(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        min_bars_per_month: int = 20
    ) -> Dict[str, Any]:
        """
        Check data completeness by verifying we have sufficient bars per time period.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date to check
            end_date: End date to check
            min_bars_per_month: Minimum expected bars per month
            
        Returns:
            Dict with completeness check results
        """
        with get_db() as db:
            # Count bars per month
            result = db.query(
                func.date_trunc('month', Bar.timestamp).label('month'),
                func.count(Bar.id).label('bar_count')
            ).filter(
                and_(
                    Bar.symbol == symbol,
                    func.date(Bar.timestamp) >= start_date,
                    func.date(Bar.timestamp) <= end_date
                )
            ).group_by(
                func.date_trunc('month', Bar.timestamp)
            ).all()
            
            # Find months with insufficient data
            incomplete_months = [
                {
                    'month': str(row.month.date()),
                    'bar_count': row.bar_count
                }
                for row in result
                if row.bar_count < min_bars_per_month
            ]
            
            issue_count = len(incomplete_months)
            severity = 'warning' if issue_count > 0 else 'info'
            
            check_result = {
                'symbol': symbol,
                'check_type': 'completeness',
                'date_range_start': start_date,
                'date_range_end': end_date,
                'issue_count': issue_count,
                'severity': severity,
                'details': json.dumps(incomplete_months) if incomplete_months else None
            }
            
            if issue_count > 0:
                self.logger.warning(f"Found {issue_count} incomplete months for {symbol}")
            else:
                self.logger.info(f"Data completeness OK for {symbol}")
            
            return check_result
    
    def check_price_anomalies(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        spike_threshold: float = 5.0,
        volume_spike_threshold: float = 10.0
    ) -> Dict[str, Any]:
        """
        Check for price and volume anomalies (spikes, outliers).
        
        Args:
            symbol: Ticker symbol
            start_date: Start date to check
            end_date: End date to check
            spike_threshold: Threshold for price spike detection (std deviations)
            volume_spike_threshold: Threshold for volume spike detection (std deviations)
            
        Returns:
            Dict with anomaly check results
        """
        with get_db() as db:
            # Fetch bars for analysis
            bars = db.query(Bar).filter(
                and_(
                    Bar.symbol == symbol,
                    func.date(Bar.timestamp) >= start_date,
                    func.date(Bar.timestamp) <= end_date
                )
            ).order_by(Bar.timestamp).all()
            
            if len(bars) < 2:
                return {
                    'symbol': symbol,
                    'check_type': 'anomaly',
                    'date_range_start': start_date,
                    'date_range_end': end_date,
                    'issue_count': 0,
                    'severity': 'info',
                    'details': 'Insufficient data for anomaly detection'
                }
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame([
                {
                    'timestamp': bar.timestamp,
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume
                }
                for bar in bars
            ])
            
            # Calculate daily returns
            df['return'] = df['close'].pct_change()
            df['log_volume'] = np.log1p(df['volume'])
            
            # Detect price spikes using z-score
            returns_mean = df['return'].mean()
            returns_std = df['return'].std()
            if returns_std > 0:
                df['return_zscore'] = (df['return'] - returns_mean) / returns_std
            else:
                df['return_zscore'] = 0
            
            # Detect volume spikes
            volume_mean = df['log_volume'].mean()
            volume_std = df['log_volume'].std()
            if volume_std > 0:
                df['volume_zscore'] = (df['log_volume'] - volume_mean) / volume_std
            else:
                df['volume_zscore'] = 0
            
            # Find anomalies
            price_anomalies = df[df['return_zscore'].abs() > spike_threshold]
            volume_anomalies = df[df['volume_zscore'] > volume_spike_threshold]
            
            anomalies = []
            
            for _, row in price_anomalies.iterrows():
                anomalies.append({
                    'timestamp': str(row['timestamp']),
                    'type': 'price_spike',
                    'return': round(float(row['return']) * 100, 2),
                    'z_score': round(float(row['return_zscore']), 2)
                })
            
            for _, row in volume_anomalies.iterrows():
                anomalies.append({
                    'timestamp': str(row['timestamp']),
                    'type': 'volume_spike',
                    'volume': int(row['volume']),
                    'z_score': round(float(row['volume_zscore']), 2)
                })
            
            issue_count = len(anomalies)
            severity = 'warning' if issue_count > 0 else 'info'
            
            check_result = {
                'symbol': symbol,
                'check_type': 'anomaly',
                'date_range_start': start_date,
                'date_range_end': end_date,
                'issue_count': issue_count,
                'severity': severity,
                'details': json.dumps(anomalies[:100]) if anomalies else None  # Limit to first 100
            }
            
            if issue_count > 0:
                self.logger.info(f"Found {issue_count} anomalies for {symbol}")
            else:
                self.logger.info(f"No anomalies found for {symbol}")
            
            return check_result
    
    def log_check_result(self, check_result: Dict[str, Any]) -> None:
        """
        Log a data quality check result to the database.
        
        Args:
            check_result: Dict with check results
        """
        with get_db() as db:
            log_entry = DataQualityLog(
                symbol=check_result['symbol'],
                check_type=check_result['check_type'],
                severity=check_result['severity'],
                check_time=datetime.utcnow(),
                date_range_start=check_result.get('date_range_start'),
                date_range_end=check_result.get('date_range_end'),
                issue_count=check_result['issue_count'],
                details=check_result.get('details'),
                resolved=False
            )
            db.add(log_entry)
            db.commit()
            
            self.logger.info(f"Logged {check_result['check_type']} check for {check_result['symbol']}")
    
    def run_all_checks(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Run all data quality checks for a symbol.
        
        Args:
            symbol: Ticker symbol
            start_date: Start date to check
            end_date: End date to check
            
        Returns:
            List of check results
        """
        self.logger.info(f"Running all QA checks for {symbol}")
        
        results = []
        
        # Check duplicates
        dup_result = self.check_duplicates(symbol, start_date, end_date)
        results.append(dup_result)
        self.log_check_result(dup_result)
        
        # Check completeness
        comp_result = self.check_completeness(symbol, start_date, end_date)
        results.append(comp_result)
        self.log_check_result(comp_result)
        
        # Check anomalies
        anom_result = self.check_price_anomalies(symbol, start_date, end_date)
        results.append(anom_result)
        self.log_check_result(anom_result)
        
        self.logger.info(f"Completed all QA checks for {symbol}")
        
        return results
    
    def get_recent_issues(
        self,
        symbol: Optional[str] = None,
        days: int = 7,
        severity: Optional[str] = None
    ) -> List[DataQualityLog]:
        """
        Get recent data quality issues.
        
        Args:
            symbol: Optional filter by symbol
            days: Number of days to look back
            severity: Optional filter by severity (info, warning, error)
            
        Returns:
            List of DataQualityLog entries
        """
        with get_db() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = db.query(DataQualityLog).filter(
                and_(
                    DataQualityLog.check_time >= cutoff_date,
                    DataQualityLog.resolved == False
                )
            )
            
            if symbol:
                query = query.filter(DataQualityLog.symbol == symbol)
            
            if severity:
                query = query.filter(DataQualityLog.severity == severity)
            
            issues = query.order_by(DataQualityLog.check_time.desc()).all()
            
            return issues
