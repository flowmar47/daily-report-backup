# API-Based Signal System - Deployment & Troubleshooting Guide

## Production Deployment

### Prerequisites
- Ubuntu 20.04+ or Debian 11+
- Python 3.9+
- Docker
- 2GB+ RAM
- 10GB+ free disk space

### 1. System Preparation

#### Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git curl wget
```

#### Install Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Application Deployment

#### Clone Repository
```bash
cd /home/ohms
git clone <repository-url> OhmsAlertsReports
cd OhmsAlertsReports/daily-report
```

#### Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r Signals/requirements.txt
```

#### Configure Environment
```bash
# Copy environment template
cp .env.template .env

# Edit with your credentials
nano .env
```

Required environment variables:
```bash
# API Keys (Primary - Required)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
TWELVE_DATA_API_KEY=your_twelve_data_key
FRED_API_KEY=your_fred_key
FINNHUB_API_KEY=your_finnhub_key

# API Keys (Fallback - Recommended for reliability)
POLYGON_API_KEY=your_polygon_key
MARKETSTACK_API_KEY=your_marketstack_key
EXCHANGERATE_API_KEY=your_exchangerate_key
FIXER_API_KEY=your_fixer_key
CURRENCY_API_KEY=your_currency_api_key
FREECURRENCY_API_KEY=your_freecurrency_key
EXCHANGERATES_API_KEY=your_exchangerates_key

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_GROUP_ID=your_group_id

# Signal Configuration
SIGNAL_PHONE_NUMBER=+1234567890
SIGNAL_GROUP_ID=your_signal_group_id
SIGNAL_API_URL=http://localhost:8080
```

#### Setup Signal API
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

#### Setup Cron Scheduling

The system uses cron for reliable scheduled execution:

```bash
# Edit crontab
crontab -e

# Add the following line for 6 AM PST execution on weekdays
0 6 * * 1-5 cd /home/ohms/OhmsAlertsReports/daily-report && source venv/bin/activate && PYTHONIOENCODING=utf-8 python enhanced_api_signals_daily.py >> logs/enhanced_api_signals_cron.log 2>&1

# Verify cron is configured
crontab -l | grep enhanced_api_signals
```

### 3. Directory Setup

```bash
# Create required directories
mkdir -p logs reports cache output

# Set permissions
chmod 755 logs reports cache output
chmod 600 .env
```

### 4. Security Configuration

#### Firewall Setup
```bash
# Allow SSH
sudo ufw allow ssh

# Enable firewall
sudo ufw enable
```

#### File Permissions
```bash
# Secure environment file
chmod 600 .env

# Secure logs directory
chmod 755 logs/
chmod 644 logs/*.log
```

## Troubleshooting Guide

### API Issues

#### 1. No Data from APIs
```bash
# Test API connectivity
python -c "
from forex_signal_integration import ForexSignalIntegration
fsi = ForexSignalIntegration()
print('Setup successful:', fsi.setup_successful)
"

# Check API keys are set
grep -E "(ALPHA_VANTAGE|TWELVE_DATA|FRED|FINNHUB)" .env

# Test individual API
python -c "
import requests
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('ALPHA_VANTAGE_API_KEY')
resp = requests.get(f'https://www.alphavantage.co/query?function=FX_DAILY&from_symbol=EUR&to_symbol=USD&apikey={key}')
print('Status:', resp.status_code)
print('Response:', resp.json().keys() if resp.ok else resp.text[:200])
"
```

**Common Causes:**
- Missing or invalid API keys
- API rate limiting
- Network connectivity issues

**Solutions:**
```bash
# Verify all API keys in .env
cat .env | grep -E "API_KEY"

# Check rate limiting logs
grep -i "rate limit" logs/enhanced_api_signals.log

# Test network connectivity
curl -I https://www.alphavantage.co
curl -I https://api.twelvedata.com
```

#### 2. Rate Limiting
```bash
# Check for rate limit errors
grep -i "429\|rate limit" logs/enhanced_api_signals.log

# View API usage patterns
grep -E "API|request|response" logs/enhanced_api_signals.log | tail -50
```

**Solutions:**
- The system automatically falls back to secondary/tertiary APIs
- Ensure all fallback API keys are configured
- Consider upgrading API tier for higher limits

### Messenger Issues

#### 1. Telegram Failures
```bash
# Test Telegram API
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Test bot permissions
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getChat?chat_id=$TELEGRAM_GROUP_ID"

# Send test message
curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
  -d "chat_id=$TELEGRAM_GROUP_ID" \
  -d "text=Test message from deployment check"
```

**Common Causes:**
- Invalid bot token
- Bot not added to group
- Group permissions
- Rate limiting

**Solutions:**
```bash
# Verify bot token format
echo $TELEGRAM_BOT_TOKEN | grep -E "^[0-9]+:[A-Za-z0-9_-]+$"

# Check group ID format (should start with - for groups)
echo $TELEGRAM_GROUP_ID

# Implement rate limiting delays between messages
```

#### 2. Signal Failures
```bash
# Check Signal API
curl http://localhost:8080/v1/about

# Check container status
sudo docker ps | grep signal-api

# View container logs
sudo docker logs signal-api --tail 50
```

**Common Causes:**
- Signal API not running
- Invalid phone number format
- Group not found
- Authentication issues

**Solutions:**
```bash
# Restart Signal API
sudo docker restart signal-api

# Verify phone number format (must include country code)
echo $SIGNAL_PHONE_NUMBER

# Check group ID
echo $SIGNAL_GROUP_ID

# Re-register device if needed
sudo docker exec signal-api signal-cli -a $SIGNAL_PHONE_NUMBER register
```

### Scheduling Issues

#### 1. Cron Not Executing
```bash
# Check cron is running
sudo systemctl status cron

# Check crontab
crontab -l

# Check cron logs
grep CRON /var/log/syslog | tail -20
```

**Solutions:**
```bash
# Restart cron service
sudo systemctl restart cron

# Test manual execution
cd /home/ohms/OhmsAlertsReports/daily-report && source venv/bin/activate && python enhanced_api_signals_daily.py
```

#### 2. Timezone Issues
```bash
# Check system timezone
timedatectl

# Set timezone to PST
sudo timedatectl set-timezone America/Los_Angeles

# Verify
date
```

### Performance Issues

#### 1. High Memory Usage
```bash
# Monitor memory usage
watch -n 1 'free -h && ps aux | grep python'

# Check for memory leaks
python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"
```

**Solutions:**
```bash
# Kill any zombie processes
pkill -f enhanced_api_signals

# Clear cache
rm -rf cache/*

# Restart with fresh state
```

#### 2. Slow API Responses
```bash
# Test API response times
time curl -s "https://www.alphavantage.co/query?function=FX_DAILY&from_symbol=EUR&to_symbol=USD&apikey=$ALPHA_VANTAGE_API_KEY" > /dev/null

# Check network latency
ping -c 4 www.alphavantage.co
```

### Network Issues

#### 1. Connection Timeouts
```bash
# Test DNS resolution
nslookup www.alphavantage.co

# Test connectivity
curl -v --connect-timeout 10 https://www.alphavantage.co

# Check firewall
sudo ufw status
```

**Solutions:**
```bash
# Update DNS servers
echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf

# Configure proxy if needed
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port
```

## Performance Optimization

### Memory Optimization
```bash
# Monitor memory usage
watch -n 5 'free -h && echo "---" && ps aux | grep python | grep -v grep'

# Clear old logs
find logs/ -name "*.log" -mtime +7 -delete
```

### Disk Optimization
```bash
# Monitor disk usage
watch -n 10 'df -h && echo "---" && du -sh logs/ reports/'

# Setup log rotation
sudo tee /etc/logrotate.d/daily-signals > /dev/null <<EOF
/home/ohms/OhmsAlertsReports/daily-report/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 ohms ohms
}
EOF
```

## Security Hardening

### Network Security
```bash
# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable

# Monitor network connections
sudo netstat -tuln | grep LISTEN
```

### Application Security
```bash
# Secure file permissions
find /home/ohms/OhmsAlertsReports -type f -name "*.py" -exec chmod 644 {} \;
find /home/ohms/OhmsAlertsReports -type d -exec chmod 755 {} \;
chmod 600 .env

# Run as non-root user
sudo chown -R ohms:ohms /home/ohms/OhmsAlertsReports
```

## Emergency Procedures

### Service Recovery
```bash
# Emergency manual execution
cd /home/ohms/OhmsAlertsReports/daily-report
source venv/bin/activate
python enhanced_api_signals_daily.py 2>&1 | tee logs/emergency.log
```

### Data Recovery
```bash
# Backup configuration
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Restore from backup
cp .env.backup.YYYYMMDD_HHMMSS .env
```

### Complete System Reset
```bash
# Stop all services
sudo docker stop signal-api

# Clear all data
rm -rf logs/* reports/* cache/*

# Restart services
sudo docker start signal-api
```

---

**Emergency Commands:**
- Manual Report: `python enhanced_api_signals_daily.py`
- Check API Status: `python -c "from forex_signal_integration import ForexSignalIntegration; print(ForexSignalIntegration().setup_successful)"`
- View Logs: `tail -f logs/enhanced_api_signals.log`
- Cron Status: `crontab -l | grep enhanced_api`

**Last Updated:** January 2026
**Version:** 3.0 (API-Based Signal Generation)
