# Agent Instructions

## AI Investing Tool Development Guidelines

### Project Context
This is a monorepo for an AI-powered algorithmic trading platform. The project follows a milestone-based development approach with M0 (Foundations) currently in progress.

### Architecture Overview

#### Monorepo Structure
```
/ai-investing-tool
  /apps
    /web          - Next.js frontend application
    /api          - FastAPI backend REST API
    /workers      - Background job workers (Celery/RQ)
  /packages
    /backtester   - Core backtesting engine (Python)
    /indicators   - Technical indicators library (Python)
    /sdk          - Client SDK for API consumption (TypeScript/Python)
  /infra          - Infrastructure as code (Docker, Terraform)
  /scripts        - Utility scripts for development and deployment
```

### Development Workflow

#### Local Development Setup
1. Run `make bootstrap` to install dependencies and set up environment
2. Start development stack with `docker compose up -d`
3. Seed demo data with `make seed-demo`
4. Run services:
   - API: `make api` (port 8000)
   - Workers: `make workers`
   - Web: `make web` (port 3000)

#### Environment Configuration
All services require environment variables defined in `.env` (use `.env.example` as template):
- Database: `POSTGRES_URL`
- Cache: `REDIS_URL`
- Storage: `S3_ENDPOINT`, `S3_BUCKET`
- Broker: `ALPACA_KEY`, `ALPACA_SECRET`

### Code Standards

#### Python (API, Workers, Packages)
- Use Python 3.11+
- Follow PEP 8 style guidelines
- Type hints required for all functions
- Use `black` for formatting
- Use `ruff` for linting
- Minimum 80% test coverage

#### TypeScript/JavaScript (Web, SDK)
- Use TypeScript for all new code
- Follow ESLint recommended rules
- Use Prettier for formatting
- Prefer functional components with hooks
- Use TailwindCSS for styling

#### Git Workflow
- Create feature branches from `main`
- Commit messages: `<type>: <description>` (e.g., `feat: add SMA indicator`)
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Keep commits atomic and focused
- Write descriptive PR descriptions

### Testing Strategy

#### Unit Tests
- Test individual functions and classes
- Mock external dependencies
- Use pytest for Python, Jest for TypeScript

#### Integration Tests
- Test API endpoints end-to-end
- Test worker job execution
- Use test database and Redis instances

#### Backtesting Tests
- Validate historical data accuracy
- Test strategy execution logic
- Verify performance calculations

### Key Principles

#### Event-Driven Architecture
The backtesting and trading systems are event-driven:
- Events: `MarketData`, `OrderFilled`, `OrderRejected`, etc.
- Handlers process events and emit new events
- Enables realistic simulation and live trading with same code

#### Immutable Audit Trail
All trading decisions and executions are logged:
- Store complete context for each decision
- Sign and hash critical data
- Never delete historical records

#### Risk Management First
- Validate all orders before submission
- Enforce position limits
- Monitor exposure in real-time
- Circuit breakers for anomalous behavior

#### Security Best Practices
- Never commit secrets to version control
- Use environment variables for configuration
- Store sensitive data in secrets manager
- Encrypt data at rest and in transit

### Working with Agents

#### When Adding Features
1. Review relevant milestone in PRD.md
2. Check tasks.md for related work items
3. Update tasks.md with new subtasks
4. Implement with appropriate tests
5. Update documentation as needed

#### When Fixing Bugs
1. Create failing test that reproduces the issue
2. Fix the bug
3. Verify test passes
4. Add regression test if applicable

#### When Refactoring
1. Ensure comprehensive test coverage exists
2. Make incremental changes
3. Run tests after each change
4. Update documentation for API changes

### Domain Knowledge

#### Backtesting Concepts
- **Bar**: OHLCV data for a time period
- **Signal**: Trading decision (buy/sell/hold)
- **Fill**: Executed order with realistic price
- **Slippage**: Difference between expected and actual fill price
- **Drawdown**: Peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return metric

#### Strategy Graph
Strategies are defined as directed acyclic graphs (DAGs):
- **Nodes**: Universe, Indicators, Rules, Sizers, Filters
- **Edges**: Data flow between nodes
- **Execution**: Topological sort ensures proper evaluation order

#### Order Management
- **Order Types**: Market, Limit, Stop, Stop-Limit
- **Order States**: Pending, Submitted, PartiallyFilled, Filled, Cancelled, Rejected
- **Time in Force**: Day, GTC, IOC, FOK

### Common Pitfalls to Avoid

1. **Look-ahead Bias**: Never use future data in backtests
2. **Survivorship Bias**: Include delisted/failed securities
3. **Overfitting**: Avoid optimizing on same data used for testing
4. **Unrealistic Fills**: Account for spread, slippage, and fees
5. **Ignoring Costs**: Transaction costs significantly impact profitability

### Resources

- [TimescaleDB Docs](https://docs.timescale.com/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [Alpaca API Docs](https://alpaca.markets/docs/)

### Support

For questions or issues:
1. Check existing documentation
2. Review related code and tests
3. Consult PRD.md and tasks.md
4. Ask for clarification if needed
