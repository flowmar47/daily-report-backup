# OhmsAlertsReports - Daily Financial Report Automation

A comprehensive financial alerts system that automatically scrapes MyMama.uk for real trading alerts and distributes them via Telegram and Signal messaging platforms.

## 🚀 System Overview

This system provides:
- **Automated daily financial reports** (6:00 AM PST weekdays)
- **Real-time MyMama.uk data scraping** with session persistence
- **Dual-platform messaging** (Telegram + Signal)
- **Heatmap generation and distribution**
- **Robust error handling and retry mechanisms**
- **Systemd service management** for 24/7 operation

## 📁 Cleaned Up Codebase Structure

```
daily-report/
├── main.py                          # Primary service entry point
├── service_runner.py                # Service management
├── config.json                      # Main configuration
├── .env                            # Environment variables
├── requirements.txt                 # Python dependencies
├── real_only_mymama_scraper.py     # Primary MyMama scraper
├── enhanced_browserbase_scraper.py # Enhanced scraper
├── messenger_compatibility.py      # Unified messenger interface
├── src/
│   ├── messengers/
│   │   └── unified_messenger.py    # Unified messaging system
│   ├── config/
│   │   └── settings.py             # Configuration management
│   └── data_processors/
│       └── template_generator.py   # Message formatting
├── utils/
│   └── env_config.py               # Environment configuration
├── logs/                           # System logs
├── reports/                        # Generated reports
├── heatmaps/                       # Generated heatmaps
└── tests/                          # Test suite
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9+
- Systemd (for service management)
- Docker (for Signal API)

### 1. Clone and Setup
```bash
cd /home/ohms/OhmsAlertsReports/daily-report
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Configuration
Create `.env` file with required credentials:
```bash
# MyMama Credentials
MYMAMA_USERNAME=your_username
MYMAMA_PASSWORD=your_password

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_GROUP_ID=your_group_id
TELEGRAM_THREAD_ID=your_thread_id

# Signal Configuration
SIGNAL_PHONE_NUMBER=+1234567890
SIGNAL_GROUP_ID=your_signal_group_id
SIGNAL_API_URL=http://localhost:8080

# Optional Settings
SIGNAL_CLI_PATH=signal-cli
CHROME_BINARY_PATH=/usr/bin/chromium-browser
```

### 3. Signal API Setup
```bash
# Setup Signal API with Docker
sudo docker run -d --name signal-api \
  --restart unless-stopped \
  -p 8080:8080 \
  -v ~/signal-api-data:/home/.local/share/signal-cli \
  -e MODE=native \
  bbernhard/signal-cli-rest-api:latest
```

### 4. Systemd Service Installation
```bash
# Install the service
sudo cp daily-alerts.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable daily-financial-report.service
sudo systemctl start daily-financial-report.service
```

## 🔧 Configuration

### Main Configuration (`config.json`)
```json
{
  "app_settings": {
    "report_time": "06:00",
    "timezone": "America/Los_Angeles",
    "report_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    "max_retries": 3,
    "retry_delay": 300
  },
  "scraping": {
    "timeout": 60000,
    "wait_for_network_idle": true,
    "user_agent": "Mozilla/5.0...",
    "request_throttling": {
      "min_delay": 3,
      "max_delay": 7
    }
  },
  "telegram": {
    "max_message_length": 4096,
    "parse_mode": "Markdown",
    "rate_limit_delay": 1
  }
}
```

## 🚀 Usage

### Manual Report Generation
```bash
# Send immediate report
python send_immediate_report.py

# Send real data only
python send_real_report_now.py

# Send heatmaps only
python send_heatmaps_only.py
```

### Service Management
```bash
# Check service status
sudo systemctl status daily-financial-report.service

# View logs
sudo journalctl -u daily-financial-report.service -f

# Restart service
sudo systemctl restart daily-financial-report.service

# Stop service
sudo systemctl stop daily-financial-report.service
```

### Testing
```bash
# Run comprehensive system test
python test_current_system.py

# Test individual components
python test_complete_structured_pipeline.py
python verify_plaintext_fix.py
```

## 📊 Monitoring & Health Checks

### System Health Check
```bash
# Run health check
python system_health_check.py

# Check service status
python service_status.py
```

### Log Monitoring
```bash
# View recent logs
tail -f logs/daily_report.log

# Check for errors
grep -i error logs/daily_report.log

# Monitor systemd logs
sudo journalctl -u daily-financial-report.service --since "1 hour ago"
```

### Performance Monitoring
```bash
# Check system resources
free -h
df -h
ps aux | grep python

# Monitor network connectivity
curl -s http://localhost:8080/v1/about  # Signal API
curl -s https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe  # Telegram API
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Service Not Starting
```bash
# Check service status
sudo systemctl status daily-financial-report.service

# View detailed logs
sudo journalctl -u daily-financial-report.service -n 50

# Check configuration
python -c "import json; json.load(open('config.json'))"
```

#### 2. MyMama Scraping Failures
```bash
# Test scraper manually
python -c "from real_only_mymama_scraper import RealOnlyMyMamaScraper; scraper = RealOnlyMyMamaScraper(); print('Scraper initialized')"

# Check credentials
echo $MYMAMA_USERNAME
echo $MYMAMA_PASSWORD

# Test browser setup
python test_real_authentication.py
```

#### 3. Messenger Failures
```bash
# Test Telegram
python -c "from messenger_compatibility import TelegramMessenger; tg = TelegramMessenger(); print('Telegram initialized')"

# Test Signal
python -c "from messenger_compatibility import SignalMessenger; sig = SignalMessenger(); print('Signal initialized')"

# Check Signal API
curl http://localhost:8080/v1/about
```

#### 4. Import Errors
```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Verify virtual environment
echo $VIRTUAL_ENV
which python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Recovery Procedures

#### Service Recovery
```bash
# Restart service
sudo systemctl restart daily-financial-report.service

# Check if running
ps aux | grep main.py

# Manual start if needed
cd /home/ohms/OhmsAlertsReports/daily-report
source venv/bin/activate
nohup python main.py > logs/manual_start.log 2>&1 &
```

#### Signal API Recovery
```bash
# Restart Signal API
sudo docker restart signal-api

# Check container status
sudo docker ps | grep signal-api

# View container logs
sudo docker logs signal-api
```

#### Browser Session Recovery
```bash
# Clear browser sessions
rm -rf browser_sessions/*

# Clear cache
rm -rf cache/*

# Restart service
sudo systemctl restart daily-financial-report.service
```

## 📈 Performance Optimization

### Memory Management
- Browser sessions are automatically cleaned up
- Log rotation is configured (7 days retention)
- Cache TTL is set to 1 hour

### Rate Limiting
- Telegram: 1 second delay between messages
- Signal: 2 second delay between messages
- MyMama: 3-7 second delay between requests

### Error Handling
- Circuit breaker protection for messaging platforms
- Exponential backoff for retries
- Graceful degradation when services are unavailable

## 🔒 Security

### Credential Management
- All credentials stored in `.env` file
- File permissions: `chmod 600 .env`
- No credentials in code or logs

### Network Security
- HTTPS for all API communications
- User agent rotation for scraping
- Rate limiting to prevent abuse

### Data Privacy
- No PII stored in logs
- Data anonymization for debugging
- Secure session management

## 📝 Development

### Adding New Messengers
1. Implement in `src/messengers/unified_messenger.py`
2. Add compatibility wrapper in `messenger_compatibility.py`
3. Update configuration in `config.json`
4. Add tests in `tests/` directory

### Adding New Scrapers
1. Create new scraper class
2. Implement required methods
3. Add to `main.py` collection logic
4. Update error handling

### Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_unified_suite.py::TestDailyReportSystem -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## 📞 Support

### Log Locations
- Application logs: `logs/daily_report.log`
- Systemd logs: `sudo journalctl -u daily-financial-report.service`
- Docker logs: `sudo docker logs signal-api`

### Debug Mode
Enable debug logging in `config.json`:
```json
{
  "monitoring": {
    "log_level": "DEBUG"
  }
}
```

### Emergency Contacts
- Service restart: `sudo systemctl restart daily-financial-report.service`
- Manual report: `python send_immediate_report.py`
- Health check: `python system_health_check.py`

---

**System Status**: ✅ Production Ready  
**Last Updated**: June 24, 2025  
**Version**: 2.0 (Cleaned Up Structure) 