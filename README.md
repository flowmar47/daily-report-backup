# Daily Financial Report - API-Based Signal Generation System

A professional forex signal generation system that delivers validated trading signals via Signal and Telegram messaging platforms. The system uses live market data from multiple API sources with intelligent fallback protection.

## System Overview

This system provides:
- **Automated daily forex signals** (6:00 AM PST weekdays)
- **Live API data retrieval** from 8+ financial data sources
- **Multi-factor signal analysis** (Technical 75%, Economic 20%, Geopolitical 5%)
- **3-source price validation** with variance checking
- **Dual-platform messaging** (Telegram + Signal)
- **Cron-based scheduling** for reliable execution

## Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Signal Generation Pipeline                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │  API Layer   │───>│   Analysis   │───>│   Signals    │              │
│  │  (8 sources) │    │   Engine     │    │  Generation  │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│         │                   │                    │                       │
│         v                   v                    v                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │    Price     │    │  Technical   │    │   Message    │              │
│  │  Validation  │    │  + Economic  │    │  Formatting  │              │
│  │  (3-source)  │    │  + Sentiment │    │  & Delivery  │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
daily-report/
├── enhanced_api_signals_daily.py    # Main entry point
├── forex_signal_integration.py      # API integration bridge
├── Signals/                         # Analysis subsystem
│   ├── src/
│   │   ├── signal_generator.py      # Multi-factor analysis engine
│   │   ├── data_fetcher.py          # Multi-API data fetching
│   │   ├── technical_analysis.py    # RSI, MACD, Bollinger Bands
│   │   ├── economic_analyzer.py     # Interest rates, indicators
│   │   ├── sentiment_analyzer.py    # News sentiment analysis
│   │   ├── price_validator.py       # 3-source price validation
│   │   ├── rate_limiter.py          # API rate limiting
│   │   └── report_generator.py      # Output formatting
│   └── tests/                       # Test suite
├── src/
│   ├── messengers/                  # Messaging integrations
│   ├── config/                      # Configuration management
│   └── data_processors/             # Message formatting
├── logs/                            # Application logs
└── reports/                         # Generated reports
```

## API Integration

### Data Sources

The system integrates with multiple financial APIs with intelligent fallback protection:

**Primary APIs** (500-800 calls/day):
- **Alpha Vantage** - Comprehensive forex data
- **Twelve Data** - Real-time market data
- **FRED API** - Economic indicators and interest rates
- **Finnhub** - Market sentiment and news data

**Secondary APIs** (fallback):
- **Polygon.io** - Professional market data
- **MarketStack** - Historical and real-time data
- **ExchangeRate-API** - Currency conversion rates

**Tertiary APIs** (additional fallback):
- **Fixer.io** - Foreign exchange rates
- **CurrencyAPI** - Multi-source currency data
- **FreeCurrencyAPI** - Backup currency rates

### Price Validation

Every price is validated through a 3-source verification process:
- Prices must agree within acceptable tolerance
- Real-time validation (no stale data)
- Automatic failover if primary sources unavailable

## Installation & Setup

### Prerequisites
- Python 3.9+
- Docker (for Signal API)

### 1. Clone and Setup

```bash
cd /home/ohms/OhmsAlertsReports/daily-report
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r Signals/requirements.txt
```

### 2. Environment Configuration

Create `.env` file with required credentials:

```bash
# API Keys (Primary)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
TWELVE_DATA_API_KEY=your_twelve_data_key
FRED_API_KEY=your_fred_key
FINNHUB_API_KEY=your_finnhub_key

# API Keys (Fallback)
POLYGON_API_KEY=your_polygon_key
MARKETSTACK_API_KEY=your_marketstack_key
EXCHANGERATE_API_KEY=your_exchangerate_key
FIXER_API_KEY=your_fixer_key
CURRENCY_API_KEY=your_currency_api_key
FREECURRENCY_API_KEY=your_freecurrency_key

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_GROUP_ID=your_group_id

# Signal Configuration
SIGNAL_PHONE_NUMBER=+1234567890
SIGNAL_GROUP_ID=your_signal_group_id
SIGNAL_API_URL=http://localhost:8080
```

### 3. Signal API Setup

```bash
# Create data directory
mkdir -p ~/signal-api-data

# Run Signal API container
sudo docker run -d --name signal-api \
  --restart unless-stopped \
  -p 8080:8080 \
  -v ~/signal-api-data:/home/.local/share/signal-cli \
  -e MODE=native \
  bbernhard/signal-cli-rest-api:latest

# Verify Signal API is running
curl http://localhost:8080/v1/about
```

### 4. Cron Scheduling

The system uses cron for scheduled execution at 6 AM PST on weekdays:

```bash
# Edit crontab
crontab -e

# Add the following line
0 6 * * 1-5 cd /home/ohms/OhmsAlertsReports/daily-report && source venv/bin/activate && PYTHONIOENCODING=utf-8 python enhanced_api_signals_daily.py >> logs/enhanced_api_signals_cron.log 2>&1
```

## Usage

### Manual Execution

```bash
# Full signal generation and delivery
cd /home/ohms/OhmsAlertsReports/daily-report
source venv/bin/activate
python enhanced_api_signals_daily.py

# Test analysis without messaging
python analysis_demo.py

# Quick single-pair analysis
python quick_analysis_demo.py
```

### Testing API Connectivity

```bash
# Test forex signal integration
python -c "from forex_signal_integration import ForexSignalIntegration; fsi = ForexSignalIntegration(); print('Setup successful:', fsi.setup_successful)"

# Test full signal generation
python -c "
import asyncio
from forex_signal_integration import ForexSignalIntegration
async def test():
    fsi = ForexSignalIntegration()
    result = await fsi.generate_forex_signals()
    print('Has real data:', result.get('has_real_data', False))
    print('Active signals:', result.get('active_signals', 0))
asyncio.run(test())
"
```

### Monitoring

```bash
# View application logs
tail -f logs/enhanced_api_signals.log

# View cron execution logs
tail -f logs/enhanced_api_signals_cron.log

# Check cron schedule
crontab -l | grep enhanced_api_signals
```

## Signal Analysis

### Multi-Factor Analysis

The system uses a weighted multi-factor approach:

| Factor | Weight | Components |
|--------|--------|------------|
| Technical | 75% | RSI, MACD, Bollinger Bands, candlestick patterns |
| Economic | 20% | Interest rate differentials, economic indicators |
| Geopolitical | 5% | Market sentiment, event impact |

### Signal Categories

- **Strong Signal** (Confidence > 0.7): High probability trading opportunity
- **Medium Signal** (Confidence 0.5-0.7): Moderate probability opportunity
- **Hold** (Confidence < 0.5): No clear trading signal

### Output Format

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
Confidence: 72.5%
Signal Category: Strong
Target: 100 pips
Risk/Reward: 1:2.5

Enhanced API Analysis - 3 signals
Real market data from validated sources
```

## Troubleshooting

### No Signals Generated

```bash
# Check API connectivity
python -c "from forex_signal_integration import ForexSignalIntegration; fsi = ForexSignalIntegration(); print('Setup:', fsi.setup_successful)"

# Test analysis pipeline
python quick_analysis_demo.py

# Check API keys in .env
grep -E "(ALPHA_VANTAGE|TWELVE_DATA|FRED|FINNHUB)" .env
```

### Rate Limiting Issues

The system automatically falls back to secondary/tertiary APIs when rate limits are hit. If all APIs are rate limited:
- Check logs for "Rate limit hit" messages
- Verify all fallback API keys are configured
- Wait for rate limit windows to reset

### Message Delivery Failures

```bash
# Test Telegram
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Test Signal API
curl http://localhost:8080/v1/about

# Check credentials
grep -E "(TELEGRAM|SIGNAL)" .env
```

## Data Quality Assurance

### Key Principles

- **API-Only Data**: No web scraping or browser automation
- **Multi-Source Validation**: Prices verified from 3+ sources
- **Real Data Only**: Zero tolerance for synthetic/fake data
- **Graceful Failure**: System fails gracefully without real data

### Confidence Scoring

All signals include confidence levels (0.0-1.0 scale):
- Only signals with confidence >= 0.6 are transmitted
- Confidence based on indicator agreement and data quality
- Historical validation against past performance

## Development

### Running Tests

```bash
# Full analysis demonstration
python analysis_demo.py

# Quick single-pair test
python quick_analysis_demo.py

# Test message formatting
python verify_plaintext_fix.py
```

### Adding New API Sources

1. Add API credentials to `.env`
2. Implement fetcher in `Signals/src/data_fetcher.py`
3. Add to fallback chain in configuration
4. Update rate limiting in `Signals/src/rate_limiter.py`

---

**System Status**: Production Ready
**Last Updated**: January 2026
**Version**: 3.0 (API-Based Signal Generation)
