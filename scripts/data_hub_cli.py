"""
CLI tool for manual data hub operations.
"""
import argparse
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


def add_symbol(args):
    """Add a new symbol to track."""
    service = DataIngestionService()
    success = service.add_symbol(
        symbol=args.symbol,
        name=args.name,
        exchange=args.exchange,
        asset_type=args.asset_type,
        sector=args.sector,
        industry=args.industry
    )
    
    if success:
        print(f"Successfully added symbol: {args.symbol}")
    else:
        print(f"Symbol {args.symbol} already exists")


def ingest_data(args):
    """Ingest data for a symbol."""
    service = DataIngestionService()
    
    # Parse dates
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
    else:
        start_date = datetime.now().date() - timedelta(days=365)
    
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
    else:
        end_date = datetime.now().date()
    
    print(f"Ingesting data for {args.symbol} from {start_date} to {end_date}")
    count = service.ingest_symbol_data(args.symbol, start_date, end_date)
    print(f"Successfully ingested {count} bars")


def repair_data(args):
    """Repair missing bars for a symbol."""
    service = DataIngestionService()
    
    print(f"Repairing missing data for {args.symbol} (lookback: {args.lookback_days} days)")
    count = service.repair_missing_bars(args.symbol, args.lookback_days)
    print(f"Repaired {count} missing bars")


def ingest_corporate_actions(args):
    """Ingest corporate actions for a symbol."""
    service = DataIngestionService()
    
    # Parse dates
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
    else:
        start_date = datetime.now().date() - timedelta(days=365)
    
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
    else:
        end_date = datetime.now().date()
    
    print(f"Ingesting corporate actions for {args.symbol}")
    count = service.ingest_corporate_actions(args.symbol, start_date, end_date)
    print(f"Successfully ingested {count} corporate actions")


def run_qa_checks(args):
    """Run data quality checks."""
    qa_service = DataQualityService()
    
    # Parse dates
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
    else:
        start_date = datetime.now().date() - timedelta(days=30)
    
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
    else:
        end_date = datetime.now().date()
    
    print(f"Running QA checks for {args.symbol} from {start_date} to {end_date}")
    results = qa_service.run_all_checks(args.symbol, start_date, end_date)
    
    print("\nResults:")
    for result in results:
        print(f"\n{result['check_type'].upper()}:")
        print(f"  Severity: {result['severity']}")
        print(f"  Issues: {result['issue_count']}")
        if result.get('details'):
            print(f"  Details: {result['details'][:200]}...")


def list_symbols(args):
    """List all tracked symbols."""
    service = DataIngestionService()
    symbols = service.fetch_symbols(active_only=not args.all)
    
    if args.all:
        print(f"All symbols ({len(symbols)}):")
    else:
        print(f"Active symbols ({len(symbols)}):")
    
    for symbol in symbols:
        print(f"  - {symbol}")


def view_issues(args):
    """View recent data quality issues."""
    qa_service = DataQualityService()
    
    issues = qa_service.get_recent_issues(
        symbol=args.symbol,
        days=args.days,
        severity=args.severity
    )
    
    if not issues:
        print("No issues found")
        return
    
    print(f"Found {len(issues)} issues:\n")
    for issue in issues:
        print(f"{issue.symbol} - {issue.check_type} ({issue.severity})")
        print(f"  Time: {issue.check_time}")
        print(f"  Issues: {issue.issue_count}")
        if issue.details:
            print(f"  Details: {issue.details[:200]}...")
        print()


def main():
    parser = argparse.ArgumentParser(description='Data Hub CLI Tool')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Add symbol command
    add_parser = subparsers.add_parser('add-symbol', help='Add a new symbol')
    add_parser.add_argument('symbol', help='Ticker symbol')
    add_parser.add_argument('--name', help='Company/asset name')
    add_parser.add_argument('--exchange', help='Exchange')
    add_parser.add_argument('--asset-type', default='equity', help='Asset type')
    add_parser.add_argument('--sector', help='Sector')
    add_parser.add_argument('--industry', help='Industry')
    
    # Ingest data command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest data for a symbol')
    ingest_parser.add_argument('symbol', help='Ticker symbol')
    ingest_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    ingest_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    
    # Repair data command
    repair_parser = subparsers.add_parser('repair', help='Repair missing data')
    repair_parser.add_argument('symbol', help='Ticker symbol')
    repair_parser.add_argument('--lookback-days', type=int, default=30, help='Days to look back')
    
    # Corporate actions command
    actions_parser = subparsers.add_parser('corporate-actions', help='Ingest corporate actions')
    actions_parser.add_argument('symbol', help='Ticker symbol')
    actions_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    actions_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    
    # QA checks command
    qa_parser = subparsers.add_parser('qa-check', help='Run QA checks')
    qa_parser.add_argument('symbol', help='Ticker symbol')
    qa_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    qa_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    
    # List symbols command
    list_parser = subparsers.add_parser('list-symbols', help='List tracked symbols')
    list_parser.add_argument('--all', action='store_true', help='Include inactive symbols')
    
    # View issues command
    issues_parser = subparsers.add_parser('view-issues', help='View recent QA issues')
    issues_parser.add_argument('--symbol', help='Filter by symbol')
    issues_parser.add_argument('--days', type=int, default=7, help='Days to look back')
    issues_parser.add_argument('--severity', choices=['info', 'warning', 'error'], help='Filter by severity')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == 'add-symbol':
        add_symbol(args)
    elif args.command == 'ingest':
        ingest_data(args)
    elif args.command == 'repair':
        repair_data(args)
    elif args.command == 'corporate-actions':
        ingest_corporate_actions(args)
    elif args.command == 'qa-check':
        run_qa_checks(args)
    elif args.command == 'list-symbols':
        list_symbols(args)
    elif args.command == 'view-issues':
        view_issues(args)


if __name__ == '__main__':
    main()
