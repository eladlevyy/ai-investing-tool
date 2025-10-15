"""Create market data tables

Revision ID: 001_init_market_data
Revises: 
Create Date: 2025-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_init_market_data'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create symbol_map table
    op.create_table(
        'symbol_map',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('exchange', sa.String(length=50), nullable=True),
        sa.Column('asset_type', sa.String(length=50), nullable=True),
        sa.Column('sector', sa.String(length=100), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('data_source', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol'),
        schema='market_data'
    )
    op.create_index('idx_symbol_map_symbol', 'symbol_map', ['symbol'], unique=False, schema='market_data')
    
    # Create bars table (will be converted to hypertable after creation)
    op.create_table(
        'bars',
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('open', sa.Float(), nullable=False),
        sa.Column('high', sa.Float(), nullable=False),
        sa.Column('low', sa.Float(), nullable=False),
        sa.Column('close', sa.Float(), nullable=False),
        sa.Column('volume', sa.BigInteger(), nullable=False),
        sa.Column('adjusted_close', sa.Float(), nullable=True),
        sa.Column('split_adjusted', sa.Boolean(), nullable=False),
        sa.Column('dividend_adjusted', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint('open > 0', name='ck_bars_open_positive'),
        sa.CheckConstraint('high > 0', name='ck_bars_high_positive'),
        sa.CheckConstraint('low > 0', name='ck_bars_low_positive'),
        sa.CheckConstraint('close > 0', name='ck_bars_close_positive'),
        sa.CheckConstraint('volume >= 0', name='ck_bars_volume_non_negative'),
        sa.CheckConstraint('high >= low', name='ck_bars_high_gte_low'),
        sa.CheckConstraint('high >= open', name='ck_bars_high_gte_open'),
        sa.CheckConstraint('high >= close', name='ck_bars_high_gte_close'),
        sa.CheckConstraint('low <= open', name='ck_bars_low_lte_open'),
        sa.CheckConstraint('low <= close', name='ck_bars_low_lte_close'),
        sa.PrimaryKeyConstraint('symbol', 'timestamp'),
        schema='market_data'
    )
    op.create_index('idx_bars_symbol_time', 'bars', ['symbol', 'timestamp'], unique=False, schema='market_data')
    op.create_index('idx_bars_timestamp', 'bars', ['timestamp'], unique=False, schema='market_data')
    
    # Convert bars table to TimescaleDB hypertable
    # Note: This is a raw SQL command specific to TimescaleDB
    op.execute("""
        SELECT create_hypertable(
            'market_data.bars',
            'timestamp',
            chunk_time_interval => INTERVAL '1 month',
            if_not_exists => TRUE
        );
    """)
    
    # Create corporate_actions table
    op.create_table(
        'corporate_actions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('action_type', sa.String(length=20), nullable=False),
        sa.Column('ex_date', sa.Date(), nullable=False),
        sa.Column('split_ratio', sa.Float(), nullable=True),
        sa.Column('dividend_amount', sa.Float(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='market_data'
    )
    op.create_index('idx_corp_actions_symbol_date', 'corporate_actions', ['symbol', 'ex_date'], unique=False, schema='market_data')
    op.create_index('idx_corp_actions_type', 'corporate_actions', ['action_type'], unique=False, schema='market_data')
    
    # Create data_quality_log table
    op.create_table(
        'data_quality_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('check_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('check_time', sa.DateTime(), nullable=False),
        sa.Column('date_range_start', sa.Date(), nullable=True),
        sa.Column('date_range_end', sa.Date(), nullable=True),
        sa.Column('issue_count', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='market_data'
    )
    op.create_index('idx_dq_log_symbol_check_time', 'data_quality_log', ['symbol', 'check_type', 'check_time'], unique=False, schema='market_data')
    op.create_index('idx_dq_log_check_time', 'data_quality_log', ['check_time'], unique=False, schema='market_data')


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_dq_log_check_time', table_name='data_quality_log', schema='market_data')
    op.drop_index('idx_dq_log_symbol_check_time', table_name='data_quality_log', schema='market_data')
    op.drop_table('data_quality_log', schema='market_data')
    
    op.drop_index('idx_corp_actions_type', table_name='corporate_actions', schema='market_data')
    op.drop_index('idx_corp_actions_symbol_date', table_name='corporate_actions', schema='market_data')
    op.drop_table('corporate_actions', schema='market_data')
    
    op.drop_index('idx_bars_timestamp', table_name='bars', schema='market_data')
    op.drop_index('idx_bars_symbol_time', table_name='bars', schema='market_data')
    op.drop_table('bars', schema='market_data')
    
    op.drop_index('idx_symbol_map_symbol', table_name='symbol_map', schema='market_data')
    op.drop_table('symbol_map', schema='market_data')
