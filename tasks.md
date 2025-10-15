# Tasks & Roadmap

## M0: Foundations (In Progress)

### Project Scaffolding
- [x] Create folder structure
  - [x] `/apps/web` - Next.js frontend
  - [x] `/apps/api` - FastAPI backend
  - [x] `/apps/workers` - Background workers
  - [x] `/packages/backtester` - Backtesting engine
  - [x] `/packages/indicators` - Technical indicators
  - [x] `/packages/sdk` - Client SDK
  - [x] `/infra` - Infrastructure code
  - [x] `/scripts` - Utility scripts

### Documentation
- [x] Create PRD.md with project overview and milestones
- [x] Create agent.md with development guidelines
- [x] Create tasks.md for tracking work items
- [ ] Add architecture diagrams
- [ ] Document API contracts
- [ ] Write deployment guide

### Development Environment
- [x] Create Makefile with key targets
  - [x] `bootstrap` - Install dependencies
  - [x] `seed-demo` - Load demo data
  - [x] `api` - Run FastAPI server
  - [x] `workers` - Run background workers
  - [x] `web` - Run Next.js dev server
- [x] Create docker-compose.yml
  - [x] PostgreSQL with TimescaleDB extension
  - [x] Redis for caching and queues
  - [x] MinIO for S3-compatible storage
  - [x] Grafana for monitoring
- [x] Create .gitignore for Python and Node.js
- [x] Create .env.example with all required variables

### Initial Code Setup
- [ ] Initialize Next.js app in `/apps/web`
  - [ ] Set up TailwindCSS
  - [ ] Configure TypeScript
  - [ ] Add basic layout and routing
- [ ] Initialize FastAPI app in `/apps/api`
  - [ ] Set up project structure
  - [ ] Configure database connection
  - [ ] Add health check endpoint
- [ ] Set up worker framework in `/apps/workers`
  - [ ] Choose between Celery and RQ
  - [ ] Configure task queue
  - [ ] Add example worker task
- [ ] Initialize Python packages
  - [ ] Set up pytest for testing
  - [ ] Configure linting and formatting
  - [ ] Add package structure

### CI/CD Pipeline
- [ ] Set up GitHub Actions
  - [ ] Linting workflow
  - [ ] Testing workflow
  - [ ] Build workflow
- [ ] Configure pre-commit hooks
  - [ ] Black/Ruff for Python
  - [ ] Prettier/ESLint for TypeScript
  - [ ] Commit message validation

## M1: Core Backtesting Engine

### Data Management
- [ ] Design TimescaleDB schema for OHLCV data
- [ ] Implement data ingestion pipeline
- [ ] Add data validation and cleaning
- [ ] Create data provider interface
- [ ] Integrate with free data sources (Yahoo Finance, Alpha Vantage)

### Backtesting Engine
- [ ] Implement event-driven backtest simulator
- [ ] Add order execution with realistic fills
- [ ] Implement fee and slippage models
- [ ] Create portfolio tracking
- [ ] Build performance metrics calculator
  - [ ] Return, CAGR, volatility
  - [ ] Sharpe, Sortino, Calmar ratios
  - [ ] Max drawdown, win rate
  - [ ] Trade statistics

### Indicators Library
- [ ] Implement moving averages (SMA, EMA, WMA)
- [ ] Add momentum indicators (RSI, MACD, Stochastic)
- [ ] Add volatility indicators (Bollinger Bands, ATR)
- [ ] Add volume indicators (OBV, VWAP)
- [ ] Create indicator testing framework
- [ ] Optimize indicator calculations (vectorization)

### Strategy Framework
- [ ] Design strategy graph data structure
- [ ] Implement graph validator
- [ ] Build strategy executor
- [ ] Add strategy serialization/deserialization
- [ ] Create example strategies
  - [ ] SMA crossover
  - [ ] Mean reversion
  - [ ] Momentum

### API Endpoints
- [ ] POST /backtests - Submit backtest job
- [ ] GET /backtests/:id - Get backtest status
- [ ] GET /backtests/:id/results - Get backtest results
- [ ] GET /strategies - List strategies
- [ ] POST /strategies - Create strategy
- [ ] GET /data/bars - Fetch historical data

### Testing
- [ ] Unit tests for backtest engine
- [ ] Unit tests for indicators
- [ ] Integration tests for complete backtest flow
- [ ] Performance benchmarks
- [ ] Data quality tests

## M2: Strategy Builder UI

### Visual Editor
- [ ] Implement node-based graph editor
- [ ] Add node palette (universe, indicators, rules, sizers)
- [ ] Implement drag-and-drop functionality
- [ ] Add edge connections with validation
- [ ] Implement zoom and pan
- [ ] Add minimap for navigation

### Strategy Management
- [ ] Create strategy list view
- [ ] Implement strategy CRUD operations
- [ ] Add strategy versioning
- [ ] Implement strategy cloning
- [ ] Add strategy search and filtering

### Backtest Configuration
- [ ] Create backtest configuration form
  - [ ] Date range selector
  - [ ] Symbol universe picker
  - [ ] Fee and slippage settings
  - [ ] Initial capital input
- [ ] Add validation for backtest parameters
- [ ] Implement backtest submission
- [ ] Create backtest queue management

### Results Visualization
- [ ] Implement equity curve chart
- [ ] Add returns distribution histogram
- [ ] Create drawdown chart
- [ ] Display performance metrics table
- [ ] Add trade list with filtering
- [ ] Implement trade-by-trade analysis

### User Experience
- [ ] Add keyboard shortcuts
- [ ] Implement undo/redo
- [ ] Add auto-save functionality
- [ ] Create onboarding tutorial
- [ ] Add example strategy templates

## M3: Paper Trading

### Broker Integration
- [ ] Implement Alpaca API client
- [ ] Add authentication and credential management
- [ ] Implement account info retrieval
- [ ] Add position tracking
- [ ] Implement order submission
- [ ] Handle order updates via webhooks

### Order Management System
- [ ] Design order state machine
- [ ] Implement order lifecycle tracking
- [ ] Add order validation
- [ ] Create position manager
- [ ] Implement risk checks
- [ ] Add order cancellation

### Live Execution
- [ ] Implement real-time data feed
- [ ] Create strategy execution engine
- [ ] Add scheduling for strategy runs
- [ ] Implement order routing
- [ ] Add execution monitoring
- [ ] Create alert system

### Monitoring Dashboard
- [ ] Display live positions
- [ ] Show pending orders
- [ ] Add real-time P&L tracking
- [ ] Create execution log
- [ ] Add performance charts
- [ ] Implement alert notifications

### Testing
- [ ] Integration tests with Alpaca paper API
- [ ] End-to-end tests for order flow
- [ ] Stress tests for execution engine
- [ ] Monitoring and alerting tests

## M4: Production Trading

### Risk Management
- [ ] Implement position size limits
- [ ] Add exposure limits by symbol/sector
- [ ] Create circuit breakers
- [ ] Add maximum daily loss limits
- [ ] Implement volatility-based sizing

### Compliance & Audit
- [ ] Design audit log schema
- [ ] Implement trade signing and verification
- [ ] Add immutable audit trail
- [ ] Create compliance reports
- [ ] Implement data retention policies

### Production Infrastructure
- [ ] Set up production Kubernetes cluster
- [ ] Implement high availability
- [ ] Add automated backups
- [ ] Configure monitoring and alerting
- [ ] Set up log aggregation
- [ ] Implement secrets management

### Security
- [ ] Add user authentication (OAuth)
- [ ] Implement role-based access control
- [ ] Add API rate limiting
- [ ] Implement encryption at rest
- [ ] Add security audit logging
- [ ] Conduct security review

### Performance Optimization
- [ ] Database query optimization
- [ ] Add caching strategy
- [ ] Implement connection pooling
- [ ] Optimize worker throughput
- [ ] Add performance monitoring

### Documentation & Training
- [ ] Write user guide
- [ ] Create video tutorials
- [ ] Document API thoroughly
- [ ] Add troubleshooting guide
- [ ] Create FAQ

## Future Enhancements

### Advanced Features
- [ ] Portfolio optimization
- [ ] Multi-strategy allocation
- [ ] Walk-forward analysis
- [ ] Monte Carlo simulation
- [ ] Machine learning integration
- [ ] Custom indicators in UI

### Platform Features
- [ ] Strategy marketplace
- [ ] Social features (following, sharing)
- [ ] Collaborative strategy building
- [ ] Strategy performance leaderboard
- [ ] Educational content integration

### Additional Integrations
- [ ] More broker integrations (Interactive Brokers, TD Ameritrade)
- [ ] Premium data providers
- [ ] News and sentiment data
- [ ] Fundamental data integration
- [ ] Options and futures support
