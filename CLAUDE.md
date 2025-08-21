# CLAUDE.md

This file provides guidance to Claude Code when working with the Enhanced API-Based Daily Signal System.

## System Overview

Enhanced API-based forex signal generation system that delivers validated trading signals via Signal and Telegram messengers. The system runs automatically at 6 AM PST on weekdays, providing professional forex trading signals based on comprehensive market analysis using real API data only.

## Architecture

### Core Components

**Main Application**: `enhanced_api_signals_daily.py` - Enhanced signal generation and messaging
- Integrates multiple API sources with fallback protection
- Performs technical, economic, and geopolitical analysis
- Generates high-confidence trading signals with BUY/SELL decisions
- Delivers via Signal and Telegram only (NO WhatsApp, NO heatmaps)
- Scheduled execution via cron at 6 AM PST weekdays

**Signal Generation**: `forex_signal_integration.py` - Bridge to Signals analysis system
- Coordinates API data fetching from 8 sources with intelligent fallbacks
- Manages rate limiting protection across multiple API providers
- Converts technical analysis to structured signal format
- Ensures only real market data is used (ZERO tolerance for synthetic data)

**Analysis System** (`Signals/` directory):
- `src/signal_generator.py` - Multi-factor analysis engine
  - Technical analysis (75% weight): RSI, MACD, Bollinger Bands, candlestick patterns
  - Economic analysis (20% weight): Interest rate differentials, economic indicators
  - Geopolitical analysis (5% weight): Market sentiment and event impact
- `src/data_fetcher.py` - Multi-API data fetching with fallback chains
- `src/price_validator.py` - 3-source price validation with variance checking
- `src/core/config.py` - Settings and API key management for all sources

**Message Formatting**: 
- `src/data_processors/template_generator.py` - Structured plaintext generation
- Exact format specification following plaintext requirements (NO emojis)
- Professional forex signal format with confidence scores
- Includes analysis breakdown and entry/target prices

### API Integration Architecture

**Primary APIs** (500-800 calls/day each):
- Alpha Vantage - Comprehensive forex data
- Twelve Data - Real-time market data
- FRED API - Economic indicators and interest rates
- Finnhub - Market sentiment and news data

**Secondary APIs** (fallback protection):
- Polygon.io - Professional market data
- MarketStack - Historical and real-time data
- ExchangeRate-API - Currency conversion rates

**Tertiary APIs** (additional fallbacks):
- Fixer.io - Foreign exchange rates
- CurrencyAPI - Multi-source currency data
- FreeCurrencyAPI - Backup currency rates
- ExchangeRatesAPI - Alternative rate source

### Critical Design Patterns

- **API-Only Data**: NO web scraping, NO browser automation, ONLY validated API sources
- **Multi-Source Validation**: Prices verified from 3+ sources with variance checking
- **Fallback Protection**: 8 API sources prevent rate limiting and ensure data availability
- **Real Data Only**: Zero tolerance for synthetic/fake data - system fails gracefully without real data
- **Structured Output**: Professional plaintext format with exact specification compliance
- **Dual Messaging**: Signal + Telegram only (WhatsApp removed, heatmaps separated)
- **Confidence Scoring**: All signals include confidence levels (0.0-1.0 scale)
- **Analysis Transparency**: Detailed breakdown of technical/economic/geopolitical factors

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
cd /home/ohms/OhmsAlertsReports/daily-report
source venv/bin/activate

# Verify dependencies
pip install -r requirements.txt
pip install -r Signals/requirements.txt

# Setup environment variables (required)
cp .env.template .env
# Edit .env with actual API keys and credentials
```

### Running the System
```bash
# Manual execution (testing)
cd /home/ohms/OhmsAlertsReports/daily-report
source venv/bin/activate
python enhanced_api_signals_daily.py

# Test signal generation without messaging
python analysis_demo.py

# Quick single-pair analysis
python quick_analysis_demo.py

# Test forex signal integration
python -c "from forex_signal_integration import ForexSignalIntegration; fsi = ForexSignalIntegration(); print('Setup successful:', fsi.setup_successful)"
```

### Testing and Validation
```bash
# Full analysis demonstration (recommended)
python analysis_demo.py

# Quick single-pair test
python quick_analysis_demo.py

# Test message formatting
python verify_plaintext_fix.py

# Check API connectivity
python -c "
import asyncio
from forex_signal_integration import ForexSignalIntegration
async def test():
    fsi = ForexSignalIntegration()
    result = await fsi.generate_forex_signals()
    print('Has real data:', result.get('has_real_data', False))
asyncio.run(test())
"
```

### Scheduling Management
```bash
# Check current cron schedule
crontab -l | grep enhanced_api_signals

# View cron execution logs
tail -f logs/enhanced_api_signals_cron.log

# View application logs
tail -f logs/enhanced_api_signals.log

# Manual execution with logging
python enhanced_api_signals_daily.py 2>&1 | tee logs/manual_execution.log
```

## Configuration

### Environment Variables (.env)
```bash
# Messaging platforms
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_GROUP_ID=your_telegram_group_id
SIGNAL_PHONE_NUMBER=+1234567890
SIGNAL_GROUP_ID=your_signal_group_id

# Primary APIs
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
TWELVE_DATA_API_KEY=your_twelve_data_key
FRED_API_KEY=your_fred_key
FINNHUB_API_KEY=your_finnhub_key

# Fallback APIs (for rate limit protection)
POLYGON_API_KEY=your_polygon_key
MARKETSTACK_API_KEY=your_marketstack_key
EXCHANGERATE_API_KEY=your_exchangerate_key
FIXER_API_KEY=your_fixer_key
CURRENCY_API_KEY=your_currency_api_key
FREECURRENCY_API_KEY=your_freecurrency_key
EXCHANGERATES_API_KEY=your_exchangerates_key
```

### Analysis Configuration
Analysis weights and thresholds configured in `Signals/src/core/config.py`:
- Technical Analysis: 75% weight
- Economic Analysis: 20% weight  
- Geopolitical Analysis: 5% weight
- Strong Signal Threshold: 0.7
- Medium Signal Threshold: 0.5

### Scheduling Configuration
Cron job runs weekdays at 6 AM PST:
```bash
0 6 * * 1-5 cd /home/ohms/OhmsAlertsReports/daily-report && source venv/bin/activate && PYTHONIOENCODING=utf-8 python enhanced_api_signals_daily.py >> logs/enhanced_api_signals_cron.log 2>&1
```

## Data Flow Architecture

1. **Scheduled Trigger** → Cron job executes at 6 AM PST weekdays
2. **System Initialization** → Load API keys, initialize signal integration
3. **API Data Collection** → Fetch from multiple sources with intelligent fallbacks
4. **Price Validation** → 3-source verification with variance checking
5. **Technical Analysis** → RSI, MACD, Bollinger Bands, pattern recognition
6. **Economic Analysis** → Interest rate differentials, economic calendar events
7. **Geopolitical Analysis** → Market sentiment and event impact assessment
8. **Signal Generation** → BUY/SELL decisions with confidence scores
9. **Message Formatting** → Structured plaintext template generation
10. **Dual Delivery** → Concurrent Signal and Telegram messaging
11. **Logging & Monitoring** → Comprehensive execution logs

## Signal Quality Assurance

### Price Validation Process
- **3-Source Verification**: Every price validated against multiple APIs
- **Variance Checking**: Prices must agree within acceptable tolerance
- **Real-Time Validation**: No cached or stale price data accepted
- **Fallback Chains**: Automatic failover if primary sources unavailable

### Analysis Integrity
- **Multi-Factor Scoring**: Technical + Economic + Geopolitical analysis
- **Confidence Metrics**: All signals include confidence scores (0.6+ for transmission)
- **Historical Validation**: Signals tested against historical performance
- **No Synthetic Data**: System fails gracefully rather than use fake data

### Output Format Standards
```
FOREX TRADING SIGNALS
Generated: 2025-08-18 06:00 PST

FOREX PAIRS

Pair: USDJPY
High: 147.58301
Average: 147.28301
Low: 146.98301
MT4 Action: MT4 BUY
Exit: 148.28301

Enhanced API Analysis - 3 signals
Real market data from validated sources
```

## Troubleshooting

### Common Issues

**No Signals Generated**:
```bash
# Check API connectivity
python -c "from forex_signal_integration import ForexSignalIntegration; fsi = ForexSignalIntegration(); print('Setup:', fsi.setup_successful)"

# Test analysis pipeline
python quick_analysis_demo.py

# Check API keys
grep -E "(ALPHA_VANTAGE|TWELVE_DATA|FRED|FINNHUB)" .env
```

**Rate Limiting Issues**:
- System automatically falls back to secondary/tertiary APIs
- Check logs for "Rate limit hit" messages
- Verify all fallback API keys are configured

**Message Delivery Failures**:
```bash
# Test manual execution
python enhanced_api_signals_daily.py

# Check messaging credentials
grep -E "(TELEGRAM|SIGNAL)" .env

# Test individual platforms
# Manual testing code available in script
```

**Cron Execution Issues**:
```bash
# Check cron schedule
crontab -l

# View cron logs
tail -f logs/enhanced_api_signals_cron.log

# Test manual execution in cron environment
cd /home/ohms/OhmsAlertsReports/daily-report && source venv/bin/activate && python enhanced_api_signals_daily.py
```

### Log Analysis
- **Application logs**: `logs/enhanced_api_signals.log`
- **Cron execution**: `logs/enhanced_api_signals_cron.log`
- **Analysis demos**: `logs/analysis_demo.log`

## Important Notes

### What This System Does
- ✅ **API-based signal generation** with 8 fallback sources
- ✅ **Multi-factor analysis** (Technical 75%, Economic 20%, Geopolitical 5%)
- ✅ **3-source price validation** with variance checking
- ✅ **Professional signal format** with confidence scores
- ✅ **Signal + Telegram messaging** with concurrent delivery
- ✅ **Automated 6 AM PST execution** via cron
- ✅ **Comprehensive logging** and error handling
- ✅ **Real data only** with graceful failure

### What This System Does NOT Do
- ❌ **NO web scraping** (MyMama.uk integration removed)
- ❌ **NO browser automation** (Playwright/Selenium removed)
- ❌ **NO heatmap generation** (separated to independent system)
- ❌ **NO WhatsApp messaging** (removed from daily signals)
- ❌ **NO synthetic data** (fails gracefully instead)
- ❌ **NO systemd service** (uses cron for simplicity)

### Migration Notes
- **Deprecated files**: `main.py` and `api_signals_daily.py` are obsolete
- **New entry point**: `enhanced_api_signals_daily.py` is the current system
- **Scheduling change**: Moved from systemd to cron for reliability
- **Enhanced features**: Fallback APIs, price validation, improved analysis

This enhanced system provides professional-grade forex signals based on validated real market data with comprehensive fallback protection and multi-factor analysis.