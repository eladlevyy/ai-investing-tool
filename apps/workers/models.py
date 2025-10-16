"""
SQLAlchemy models for the market data hub.
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Date, Boolean,
    Index, UniqueConstraint, CheckConstraint, BigInteger, Text
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SymbolMap(Base):
    """
    Symbol mapping table for ticker management.
    Maps symbols to their metadata and status.
    """
    __tablename__ = 'symbol_map'
    __table_args__ = {'schema': 'market_data'}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255))
    exchange = Column(String(50))
    asset_type = Column(String(50), default='equity')  # equity, etf, etc.
    sector = Column(String(100))
    industry = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    data_source = Column(String(50), default='yfinance')  # yfinance, polygon, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<SymbolMap(symbol='{self.symbol}', name='{self.name}', is_active={self.is_active})>"


class Bar(Base):
    """
    OHLCV bar data - will be converted to TimescaleDB hypertable.
    Stores end-of-day price and volume data.
    """
    __tablename__ = 'bars'
    __table_args__ = (
        Index('idx_bars_symbol_time', 'symbol', 'timestamp'),
        Index('idx_bars_timestamp', 'timestamp'),
        CheckConstraint('open > 0', name='ck_bars_open_positive'),
        CheckConstraint('high > 0', name='ck_bars_high_positive'),
        CheckConstraint('low > 0', name='ck_bars_low_positive'),
        CheckConstraint('close > 0', name='ck_bars_close_positive'),
        CheckConstraint('volume >= 0', name='ck_bars_volume_non_negative'),
        CheckConstraint('high >= low', name='ck_bars_high_gte_low'),
        CheckConstraint('high >= open', name='ck_bars_high_gte_open'),
        CheckConstraint('high >= close', name='ck_bars_high_gte_close'),
        CheckConstraint('low <= open', name='ck_bars_low_lte_open'),
        CheckConstraint('low <= close', name='ck_bars_low_lte_close'),
        {'schema': 'market_data'}
    )
    
    symbol = Column(String(20), primary_key=True, nullable=False)
    timestamp = Column(DateTime, primary_key=True, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    adjusted_close = Column(Float)  # Adjusted for splits and dividends
    split_adjusted = Column(Boolean, default=False, nullable=False)
    dividend_adjusted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Bar(symbol='{self.symbol}', timestamp='{self.timestamp}', close={self.close})>"


class CorporateAction(Base):
    """
    Corporate actions (splits, dividends) tracking.
    """
    __tablename__ = 'corporate_actions'
    __table_args__ = (
        Index('idx_corp_actions_symbol_date', 'symbol', 'ex_date'),
        Index('idx_corp_actions_type', 'action_type'),
        {'schema': 'market_data'}
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    action_type = Column(String(20), nullable=False)  # 'split' or 'dividend'
    ex_date = Column(Date, nullable=False)  # Ex-dividend or ex-split date
    
    # Split specific fields
    split_ratio = Column(Float)  # e.g., 2.0 for 2-for-1 split
    
    # Dividend specific fields
    dividend_amount = Column(Float)  # Dividend amount per share
    
    # Metadata
    processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<CorporateAction(symbol='{self.symbol}', type='{self.action_type}', ex_date='{self.ex_date}')>"


class DataQualityLog(Base):
    """
    Data quality check results and anomaly tracking.
    """
    __tablename__ = 'data_quality_log'
    __table_args__ = (
        Index('idx_dq_log_symbol_check_time', 'symbol', 'check_type', 'check_time'),
        Index('idx_dq_log_check_time', 'check_time'),
        {'schema': 'market_data'}
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    check_type = Column(String(50), nullable=False)  # 'duplicate', 'missing', 'anomaly'
    severity = Column(String(20), nullable=False)  # 'info', 'warning', 'error'
    check_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_range_start = Column(Date)
    date_range_end = Column(Date)
    issue_count = Column(Integer, default=0)
    details = Column(Text)  # JSON or text description of issues
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime)
    
    def __repr__(self):
        return f"<DataQualityLog(symbol='{self.symbol}', check_type='{self.check_type}', severity='{self.severity}')>"
