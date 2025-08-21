# Forex Signal Generation System

A comprehensive, production-ready Python system that generates weekly forex trading signals by combining technical analysis (with emphasis on 4-hour candlestick patterns), economic indicators, news sentiment, and geopolitical events.

## Features

- **4-Hour Candlestick Pattern Analysis**: Dedicated detection of bullish/bearish patterns on 4H timeframe
- **Multi-Source Technical Analysis**: RSI, MACD, Bollinger Bands across multiple timeframes
- **Economic Fundamental Analysis**: Interest rates, GDP, inflation data from FRED
- **AI-Powered Sentiment Analysis**: News sentiment with VADER and Alpha Vantage enhancement
- **Geopolitical Event Analysis**: GDELT event impact assessment
- **Composite Signal Generation**: Intelligent weighting of all analysis components
- **Weekly Target Calculation**: Based on Average Weekly Range (AWR) with achievement probability
- **Multiple Output Formats**: Text, JSON, CSV, and HTML reports
- **Production-Ready**: Docker support, Redis caching, rate limiting, comprehensive logging
- **MT4 Compatible**: Output formatted for MetaTrader 4 usage

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd forex-signal-generator
cp .env.template .env
```

### 2. Configure API Keys

Edit `.env` file with your API keys:

```bash
# Required API keys
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
TWELVE_DATA_API_KEY=your_twelve_data_key
FRED_API_KEY=your_fred_key
FINNHUB_API_KEY=your_finnhub_key
NEWS_API_KEY=your_news_api_key
```

**Free API Key Sources:**
- [Alpha Vantage](https://www.alphavantage.co/support/#api-key) - 25 calls/day
- [Twelve Data](https://twelvedata.com/pricing) - 800 calls/day
- [FRED](https://fred.stlouisfed.org/docs/api/api_key.html) - Unlimited
- [Finnhub](https://finnhub.io/register) - 60 calls/minute
- [NewsAPI](https://newsapi.org/register) - 1000 calls/month

### 3. Docker Deployment (Recommended)

```bash
# Start the system with Redis cache
docker-compose up -d

# Generate signals immediately
docker-compose --profile manual up forex-signals-once

# View logs
docker-compose logs -f forex-signals
```

### 4. Local Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install TA-Lib (required for technical analysis)
# On Ubuntu/Debian:
sudo apt-get install build-essential
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ..
pip install TA-Lib

# Start Redis (optional, falls back to in-memory cache)
redis-server

# Run the system
python main.py --schedule  # Runs every Monday at 6 AM
python main.py --generate  # Generate signals immediately
```

## Usage Examples

### Command Line Interface

```bash
# Generate signals for default pairs
python main.py --generate

# Generate signals for specific pairs
python main.py --generate --pairs EURUSD GBPUSD USDJPY

# Generate all report formats
python main.py --generate --formats txt json csv html

# Run in test mode (no file output)
python main.py --generate --test-mode

# Schedule weekly analysis
python main.py --schedule

# Custom output directory
python main.py --generate --output-dir /path/to/reports
```

### Programmatic Usage

```python
from src.signal_generator import signal_generator
from src.report_generator import report_generator

# Generate signals
pairs = ['EURUSD', 'GBPUSD', 'USDJPY']
signals = signal_generator.generate_signals_for_pairs(pairs)

# Generate report
report = report_generator.generate_comprehensive_report(signals, 'txt')
print(report)
```

## System Architecture

### Signal Generation Process

1. **Data Collection**
   - 4H forex data from Alpha Vantage/Twelve Data
   - Economic indicators from FRED
   - News sentiment from NewsAPI/Alpha Vantage
   - Geopolitical events from GDELT

2. **Technical Analysis** (35% weight)
   - 4H candlestick pattern detection (Hammer, Engulfing, Doji, etc.)
   - Multi-timeframe indicators (RSI, MACD, Bollinger Bands)

3. **Economic Analysis** (25% weight)
   - Currency strength differential calculation
   - Interest rate, GDP, inflation comparisons
   - Economic calendar impact assessment

4. **Sentiment Analysis** (20% weight)
   - VADER sentiment with forex-specific enhancements
   - AI-powered news analysis
   - Central bank communication tone analysis

5. **Geopolitical Analysis** (10% weight)
   - GDELT event relevance and tone scoring
   - High-impact event identification

6. **4H Pattern Emphasis** (10% weight)
   - Dedicated weight for 4H candlestick patterns
   - Recent pattern prioritization

7. **Composite Scoring**
   - Weighted combination of all components
   - Confidence-adjusted signal strength
   - Trading action determination (BUY/SELL/HOLD)

8. **Weekly Target Calculation**
   - Average Weekly Range (AWR) based targets
   - Time-adjusted pip targets
   - Achievement probability calculation
   - Risk/reward ratio optimization

### Output Formats

#### Text Report (MT4 Compatible)
```
EURUSD - BUY 📈
Confidence: 75.0% ★★★★
Entry Price:     1.10500
Exit Target:     1.11800
Stop Loss:       1.09700
Target Pips:     130 pips
Success Prob:    68.0%
```

#### JSON Report (API Integration)
```json
{
  "signals": {
    "EURUSD": {
      "action": "BUY",
      "entry_price": 1.1050,
      "confidence": 0.75,
      "components": {...}
    }
  }
}
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key | None | Yes |
| `TWELVE_DATA_API_KEY` | Twelve Data API key | None | Yes |
| `FRED_API_KEY` | FRED API key | None | Yes |
| `FINNHUB_API_KEY` | Finnhub API key | None | Yes |
| `NEWS_API_KEY` | NewsAPI key | None | Yes |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `CURRENCY_PAIRS` | Pairs to analyze | `USDCAD,EURUSD,CHFJPY,USDJPY,USDCHF` | No |

### Signal Weights

The system uses adaptive weights for different analysis components:

- **Technical Analysis**: 35% (includes 4H patterns and indicators)
- **Economic Fundamentals**: 25% (currency strength differentials)
- **Market Sentiment**: 20% (news and social sentiment)
- **Geopolitical Events**: 10% (GDELT event analysis)
- **4H Candlestick Patterns**: 10% (dedicated pattern analysis)

### Risk Management

- **Maximum Stop Loss**: 200 pips
- **Minimum Target**: 100 pips
- **Risk/Reward Ratio**: 2:1 minimum
- **Position Sizing**: 1-2% account risk recommended
- **Signal Validity**: Until Friday 23:59 GMT

## API Rate Limits

The system respects API rate limits and implements intelligent fallback:

| API | Free Tier Limit | System Limit |
|-----|----------------|--------------|
| Alpha Vantage | 25 calls/day | 15 calls/day (saved for critical analysis) |
| Twelve Data | 800 calls/day | 400 calls/day |
| FRED | Unlimited | 120 calls/minute |
| Finnhub | 60 calls/minute | 60 calls/minute |
| NewsAPI | 1000 calls/month | Distributed across days |

## Caching Strategy

- **Redis Primary**: Production caching with configurable TTL
- **In-Memory Fallback**: Automatic fallback when Redis unavailable
- **Cache TTL**:
  - Forex data: 1 hour
  - Economic data: 2 hours
  - News data: 30 minutes

## Testing

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_signal_generator.py
pytest tests/test_technical_analysis.py

# Run with coverage
pytest --cov=src tests/
```

## Monitoring and Logging

- **Structured Logging**: JSON format with timestamps
- **Log Rotation**: Daily rotation with 30-day retention
- **Health Checks**: Docker health checks included
- **Error Tracking**: Comprehensive error logging with context

## Production Deployment

### Docker Compose (Recommended)

```yaml
version: '3.8'
services:
  forex-signals:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./reports:/app/reports
      - ./.env:/app/.env:ro
    depends_on:
      - redis
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: forex-signals
spec:
  replicas: 1
  selector:
    matchLabels:
      app: forex-signals
  template:
    spec:
      containers:
      - name: forex-signals
        image: forex-signals:latest
        command: ["python", "main.py", "--schedule"]
```

## Security Considerations

- **API Key Protection**: Environment variables only, never in code
- **Non-Root Container**: Docker runs as non-root user
- **Network Isolation**: Container networking with minimal exposure
- **Input Validation**: All external data validated and sanitized
- **Rate Limiting**: Prevents API abuse and quota exhaustion

## Performance Optimization

- **Parallel Processing**: Concurrent API calls where possible
- **Intelligent Caching**: Multi-tier caching strategy
- **Fallback Systems**: Graceful degradation when services unavailable
- **Memory Management**: Efficient data structures and cleanup
- **Connection Pooling**: Reused HTTP connections

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   ```
   Solution: System automatically falls back to in-memory cache
   ```

2. **API Rate Limit Exceeded**
   ```
   Solution: System implements exponential backoff and intelligent fallback
   ```

3. **Missing TA-Lib**
   ```bash
   # Install TA-Lib system dependency
   sudo apt-get install libta-lib-dev
   pip install TA-Lib
   ```

4. **Insufficient Signal Strength**
   ```
   Reason: Market conditions don't meet minimum confidence thresholds
   Action: System correctly outputs HOLD recommendation
   ```

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
python main.py --generate --test-mode
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

**RISK WARNING**: Trading foreign exchange carries a high level of risk and may not be suitable for all investors. The high degree of leverage can work against you as well as for you. Before deciding to trade foreign exchange you should carefully consider your investment objectives, level of experience, and risk appetite. This system is for educational purposes only and should not be considered as financial advice. Past performance is not indicative of future results.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review logs in the `logs/` directory