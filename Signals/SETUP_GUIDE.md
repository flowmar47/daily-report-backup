# Forex Signal Generator - Setup Guide

## 📦 Quick Start

This package contains a complete forex signal generation system with dynamic pip targeting, enhanced error handling, and comprehensive testing.

### 🚀 Installation

1. **Extract the archive**:
   ```bash
   unzip signals2.zip
   cd forex-signal-generator
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   ```

### 🔑 Required API Keys

Edit the `.env` file with your API credentials:

```env
# Required API Keys
FOREX_ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FOREX_TWELVE_DATA_API_KEY=your_twelve_data_key
FOREX_FRED_API_KEY=your_fred_key
FOREX_FINNHUB_API_KEY=your_finnhub_key
FOREX_NEWS_API_KEY=your_news_api_key

# Optional
FOREX_REDDIT_CLIENT_ID=your_reddit_client_id
FOREX_REDDIT_CLIENT_SECRET=your_reddit_client_secret
```

### 🎯 Usage

**Generate signals for specific pairs**:
```bash
python main.py --generate --pairs EURUSD GBPUSD USDJPY
```

**Schedule automatic generation**:
```bash
python main.py --schedule
```

**Run tests**:
```bash
pytest tests/ -v
```

## 🏗️ Integration into Existing Systems

### As a Python Module

```python
from src.signal_generator import signal_generator
from src.core.config import settings

# Generate signal for a specific pair
signal = signal_generator.generate_weekly_signal('EURUSD')
print(f"Action: {signal.action}, Confidence: {signal.confidence:.2%}")

# Generate multiple signals
pairs = ['EURUSD', 'GBPUSD', 'USDJPY']
signals = signal_generator.generate_signals_for_pairs(pairs)
```

### REST API Integration

Add this to your Flask/FastAPI application:

```python
from flask import Flask, jsonify
from src.signal_generator import signal_generator

app = Flask(__name__)

@app.route('/signals/<pair>')
def get_signal(pair):
    signal = signal_generator.generate_weekly_signal(pair.upper())
    return jsonify({
        'pair': signal.pair,
        'action': signal.action,
        'confidence': signal.confidence,
        'target_pips': signal.target_pips,
        'expected_timeframe': signal.components['technical'].details.get('expected_timeframe'),
        'signal_category': signal.components['technical'].details.get('signal_category')
    })
```

### Docker Deployment

```bash
# Build image
docker build -t forex-signals .

# Run with environment variables
docker run -e FOREX_ALPHA_VANTAGE_API_KEY=your_key forex-signals

# Or use docker-compose
docker-compose up
```

## 🎛️ Configuration Options

### Signal Parameters

Edit `src/core/config.py` or use environment variables:

```python
# Pip targeting (new dynamic system)
FOREX_DEFAULT_TARGET_PIPS=50          # Base target (reduced from 100)
FOREX_STRONG_SIGNAL_TARGET_PIPS=100   # Strong signals
FOREX_MEDIUM_SIGNAL_TARGET_PIPS=75    # Medium signals
FOREX_WEAK_SIGNAL_TARGET_PIPS=50      # Weak signals

# Signal thresholds
FOREX_STRONG_SIGNAL_THRESHOLD=0.7
FOREX_MEDIUM_SIGNAL_THRESHOLD=0.5
FOREX_WEAK_SIGNAL_THRESHOLD=0.3

# Risk management
FOREX_RISK_REWARD_RATIO=2.0
FOREX_MAX_STOP_LOSS_PIPS=100
```

### Analysis Weights

```python
# Customize analysis component weights
FOREX_TECHNICAL_ANALYSIS_WEIGHT=0.35
FOREX_ECONOMIC_ANALYSIS_WEIGHT=0.25
FOREX_SENTIMENT_ANALYSIS_WEIGHT=0.20
FOREX_GEOPOLITICAL_ANALYSIS_WEIGHT=0.10
FOREX_PATTERN_ANALYSIS_WEIGHT=0.10
```

## 📊 Key Features

### ✨ Enhanced Signal Generation
- **Dynamic pip targeting**: 50-150 pips based on signal strength
- **Signal categorization**: Weak/Medium/Strong/Enhanced
- **Timeframe predictions**: 1-24 hours expected achievement time
- **Technical confluence detection**: Automatic target enhancement

### 🛡️ Robust Error Handling
- **Custom exception classes** for different error types
- **Comprehensive input validation** with sanitization
- **Graceful API failure handling** with fallback strategies
- **Structured logging** with JSON output support

### 🧪 Testing & Quality
- **71 unit tests** covering critical components
- **Input validation tests** for all validators
- **Exception handling tests** for error scenarios
- **Signal generation tests** with mocked data

### ⚡ Performance Optimizations
- **Smart caching system** with LRU and TTL support
- **API rate limiting** with intelligent backoff
- **Multi-timeframe analysis** (30m, 1h, 4h, daily)
- **Concurrent request handling** with connection pooling

## 🔧 Customization Examples

### Custom Signal Processor

```python
from src.signal_generator import SignalGenerator
from src.core.config import settings

class CustomSignalProcessor(SignalGenerator):
    def __init__(self):
        super().__init__()
        # Override default thresholds
        self.signal_thresholds = {
            'strong': 0.8,    # More conservative
            'medium': 0.6,
            'weak': 0.4
        }
    
    def custom_risk_management(self, signal):
        # Add your custom risk rules
        if signal.pair == 'GBPUSD':
            signal.target_pips *= 0.8  # Reduce GBP targets
        return signal
```

### Custom Data Source

```python
from src.data_fetcher import DataFetcher

class CustomDataFetcher(DataFetcher):
    def fetch_custom_indicator(self, pair):
        # Add your custom data source
        return self.your_api_call(pair)
```

## 📈 Signal Output Format

```json
{
  "pair": "EURUSD",
  "action": "BUY",
  "confidence": 0.746,
  "signal_strength": 0.102,
  "entry_price": 1.16670,
  "target_pips": 100,
  "stop_loss": 1.16170,
  "signal_category": "Weak",
  "expected_timeframe": "8-24 hours",
  "achievement_probability": 0.149,
  "risk_reward_ratio": 2.0,
  "components": {
    "technical": {"score": 0.17, "confidence": 0.987},
    "economic": {"score": -0.05, "confidence": 0.763},
    "sentiment": {"score": 0.04, "confidence": 0.732}
  }
}
```

## 🚨 Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure all required API keys are set in `.env`
2. **Rate Limiting**: The system handles this automatically with backoff
3. **Missing Dependencies**: Run `pip install -r requirements.txt`
4. **Redis Connection**: System falls back to memory cache if Redis unavailable

### Debug Mode

```bash
# Enable debug logging
export FOREX_LOG_LEVEL=DEBUG
export FOREX_DEBUG_MODE=true
python main.py --generate --pairs EURUSD
```

### Test Configuration

```bash
# Test with mock data (no API calls)
export FOREX_USE_MOCK_DATA=true
python main.py --generate --pairs EURUSD
```

## 📞 Support

For integration support or customization requests:
- Check the comprehensive test suite in `tests/`
- Review the configuration options in `src/core/config.py`
- Examine the signal generation logic in `src/signal_generator.py`
- Use the structured logging for debugging

## 🔄 Updates

To update the system:
1. Replace the `src/` directory with new version
2. Update `requirements.txt` if needed
3. Run tests: `pytest tests/ -v`
4. Update configuration if new options available

---

**Ready to generate forex signals with enhanced accuracy and reliability!** 🚀