"""
Basic tests for the data hub implementation.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, SymbolMap, Bar, CorporateAction, DataQualityLog


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing."""
    # Note: SQLite doesn't support all PostgreSQL features (like schemas)
    # This is a basic smoke test; full testing requires PostgreSQL
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_symbol_map_creation(test_db):
    """Test creating a SymbolMap entry."""
    symbol = SymbolMap(
        symbol='TEST',
        name='Test Company',
        exchange='NYSE',
        asset_type='equity',
        is_active=True,
        data_source='test',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(symbol)
    test_db.commit()
    
    result = test_db.query(SymbolMap).filter_by(symbol='TEST').first()
    assert result is not None
    assert result.name == 'Test Company'
    assert result.is_active is True


def test_bar_creation(test_db):
    """Test creating a Bar entry."""
    bar = Bar(
        symbol='TEST',
        timestamp=datetime.utcnow(),
        open=100.0,
        high=105.0,
        low=99.0,
        close=103.0,
        volume=1000000,
        split_adjusted=False,
        dividend_adjusted=False,
        created_at=datetime.utcnow()
    )
    test_db.add(bar)
    test_db.commit()
    
    result = test_db.query(Bar).filter_by(symbol='TEST').first()
    assert result is not None
    assert result.close == 103.0
    assert result.volume == 1000000


def test_corporate_action_creation(test_db):
    """Test creating a CorporateAction entry."""
    action = CorporateAction(
        symbol='TEST',
        action_type='split',
        ex_date=datetime.utcnow().date(),
        split_ratio=2.0,
        processed=False,
        created_at=datetime.utcnow()
    )
    test_db.add(action)
    test_db.commit()
    
    result = test_db.query(CorporateAction).filter_by(symbol='TEST').first()
    assert result is not None
    assert result.action_type == 'split'
    assert result.split_ratio == 2.0


def test_data_quality_log_creation(test_db):
    """Test creating a DataQualityLog entry."""
    log = DataQualityLog(
        symbol='TEST',
        check_type='duplicate',
        severity='error',
        check_time=datetime.utcnow(),
        issue_count=5,
        details='Test details',
        resolved=False
    )
    test_db.add(log)
    test_db.commit()
    
    result = test_db.query(DataQualityLog).filter_by(symbol='TEST').first()
    assert result is not None
    assert result.check_type == 'duplicate'
    assert result.issue_count == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
