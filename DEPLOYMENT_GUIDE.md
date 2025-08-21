# OhmsAlertsReports Deployment & Troubleshooting Guide

## 🚀 Production Deployment

### Prerequisites
- Ubuntu 20.04+ or Debian 11+
- Python 3.9+
- Docker
- Systemd
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

#### Install Chrome/Chromium
```bash
# For Ubuntu/Debian
sudo apt install -y chromium-browser

# For ARM64 (Raspberry Pi)
sudo apt install -y chromium-browser
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
```

#### Configure Environment
```bash
# Copy environment template
cp env.example .env

# Edit with your credentials
nano .env
```

Required environment variables:
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

#### Install Systemd Service
```bash
# Copy service file
sudo cp daily-alerts.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable daily-financial-report.service
sudo systemctl start daily-financial-report.service
```

### 3. Monitoring Setup

#### Install Monitoring Dependencies
```bash
cd monitoring
chmod +x start_monitoring.sh
./start_monitoring.sh install
```

#### Start Monitoring Dashboard
```bash
./start_monitoring.sh start
```

The dashboard will be available at: http://localhost:5000

#### Setup Monitoring Service (Optional)
```bash
# Create monitoring service file
sudo tee /etc/systemd/system/ohms-monitoring.service > /dev/null <<EOF
[Unit]
Description=OhmsAlertsReports Monitoring Dashboard
After=network.target

[Service]
Type=simple
User=ohms
WorkingDirectory=/home/ohms/OhmsAlertsReports/daily-report
Environment=PATH=/home/ohms/OhmsAlertsReports/daily-report/venv/bin
ExecStart=/home/ohms/OhmsAlertsReports/daily-report/venv/bin/python monitoring/dashboard.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start monitoring service
sudo systemctl enable ohms-monitoring.service
sudo systemctl start ohms-monitoring.service
```

### 4. Security Configuration

#### Firewall Setup
```bash
# Allow SSH
sudo ufw allow ssh

# Allow monitoring dashboard (if external access needed)
sudo ufw allow 5000

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

# Secure configuration files
chmod 644 config.json
```

#### SSL/TLS Setup (Optional)
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Setup Nginx reverse proxy
sudo apt install -y nginx

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/ohms-monitoring > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/ohms-monitoring /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

## 🔧 Troubleshooting Guide

### Service Issues

#### 1. Service Won't Start
```bash
# Check service status
sudo systemctl status daily-financial-report.service

# View detailed logs
sudo journalctl -u daily-financial-report.service -n 50

# Check configuration
python -c "import json; json.load(open('config.json'))"

# Test manual start
cd /home/ohms/OhmsAlertsReports/daily-report
source venv/bin/activate
python main.py
```

**Common Causes:**
- Missing environment variables
- Invalid configuration file
- Permission issues
- Missing dependencies

**Solutions:**
```bash
# Verify environment variables
source .env && echo "Environment loaded"

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Fix permissions
sudo chown -R ohms:ohms /home/ohms/OhmsAlertsReports
chmod 600 .env
```

#### 2. Service Crashes Repeatedly
```bash
# Check for memory issues
free -h
ps aux | grep python

# Check disk space
df -h

# View crash logs
sudo journalctl -u daily-financial-report.service --since "1 hour ago" | grep -i error
```

**Solutions:**
```bash
# Increase system resources
sudo systemctl set-property daily-financial-report.service MemoryMax=1G

# Add restart policy
sudo systemctl edit daily-financial-report.service
# Add:
# [Service]
# Restart=always
# RestartSec=30
# StartLimitInterval=300
# StartLimitBurst=5
```

### Scraping Issues

#### 1. MyMama Authentication Fails
```bash
# Test credentials
python -c "
from real_only_mymama_scraper import RealOnlyMyMamaScraper
scraper = RealOnlyMyMamaScraper()
print('Scraper initialized successfully')
"

# Check browser setup
python test_real_authentication.py
```

**Common Causes:**
- Invalid credentials
- Website changes
- Browser compatibility issues
- Network connectivity problems

**Solutions:**
```bash
# Update browser
sudo apt update && sudo apt install -y chromium-browser

# Clear browser sessions
rm -rf browser_sessions/*

# Test network connectivity
curl -I https://mymama.uk

# Update user agent in config.json
```

#### 2. Scraping Timeouts
```bash
# Check network connectivity
ping -c 4 mymama.uk

# Test with different timeout
python -c "
import requests
response = requests.get('https://mymama.uk', timeout=30)
print(f'Status: {response.status_code}')
"
```

**Solutions:**
```bash
# Increase timeout in config.json
{
  "scraping": {
    "timeout": 120000
  }
}

# Add retry logic
# Update main.py with exponential backoff
```

### Messenger Issues

#### 1. Telegram Failures
```bash
# Test Telegram API
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Test bot permissions
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getChat?chat_id=$TELEGRAM_GROUP_ID"
```

**Common Causes:**
- Invalid bot token
- Bot not added to group
- Group permissions
- Rate limiting

**Solutions:**
```bash
# Verify bot token
echo $TELEGRAM_BOT_TOKEN

# Add bot to group with admin permissions
# Check group ID format (should start with - for groups)

# Implement rate limiting
# Add delays between messages
```

#### 2. Signal Failures
```bash
# Check Signal API
curl http://localhost:8080/v1/about

# Check container status
sudo docker ps | grep signal-api

# View container logs
sudo docker logs signal-api
```

**Common Causes:**
- Signal API not running
- Invalid phone number
- Group not found
- Authentication issues

**Solutions:**
```bash
# Restart Signal API
sudo docker restart signal-api

# Verify phone number format
echo $SIGNAL_PHONE_NUMBER

# Check group ID
echo $SIGNAL_GROUP_ID

# Re-register device if needed
sudo docker exec signal-api signal-cli -a $SIGNAL_PHONE_NUMBER register
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
# Optimize browser sessions
# Add session cleanup in main.py

# Implement memory monitoring
# Add memory limits in systemd service

# Use headless browser mode
# Update config.json
```

#### 2. High CPU Usage
```bash
# Monitor CPU usage
top -p $(pgrep -f main.py)

# Check for infinite loops
strace -p $(pgrep -f main.py) -e trace=network
```

**Solutions:**
```bash
# Add CPU limits
sudo systemctl set-property daily-financial-report.service CPUQuota=50%

# Optimize scraping intervals
# Add delays between requests

# Use async operations
# Implement connection pooling
```

### Network Issues

#### 1. Connection Timeouts
```bash
# Test DNS resolution
nslookup mymama.uk

# Test connectivity
curl -v --connect-timeout 10 https://mymama.uk

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

# Add retry logic with exponential backoff
```

#### 2. SSL/TLS Issues
```bash
# Test SSL connection
openssl s_client -connect mymama.uk:443

# Check certificate
echo | openssl s_client -servername mymama.uk -connect mymama.uk:443 2>/dev/null | openssl x509 -noout -dates
```

**Solutions:**
```bash
# Update CA certificates
sudo apt update-ca-certificates

# Disable SSL verification (not recommended for production)
# Add verify=False to requests calls

# Use custom SSL context
# Implement certificate pinning
```

### Monitoring Issues

#### 1. Dashboard Not Accessible
```bash
# Check if dashboard is running
ps aux | grep dashboard.py

# Check port availability
netstat -tuln | grep 5000

# Test local access
curl http://localhost:5000
```

**Solutions:**
```bash
# Restart monitoring
cd monitoring
./start_monitoring.sh restart

# Check firewall
sudo ufw allow 5000

# Check logs
tail -f logs/monitoring.log
```

#### 2. Metrics Not Updating
```bash
# Check metrics collection
curl http://localhost:5000/api/metrics

# Check systemd permissions
sudo systemctl status daily-financial-report.service
```

**Solutions:**
```bash
# Fix permissions
sudo usermod -aG systemd ohms

# Restart monitoring service
sudo systemctl restart ohms-monitoring.service

# Check Python dependencies
pip install psutil flask requests
```

## 📊 Performance Optimization

### Memory Optimization
```bash
# Monitor memory usage
watch -n 5 'free -h && echo "---" && ps aux | grep python | grep -v grep'

# Set memory limits
sudo systemctl set-property daily-financial-report.service MemoryMax=1G MemorySwapMax=2G
```

### CPU Optimization
```bash
# Monitor CPU usage
htop -p $(pgrep -f main.py)

# Set CPU limits
sudo systemctl set-property daily-financial-report.service CPUQuota=50%
```

### Disk Optimization
```bash
# Monitor disk usage
watch -n 10 'df -h && echo "---" && du -sh logs/ reports/'

# Setup log rotation
sudo tee /etc/logrotate.d/ohms-alerts > /dev/null <<EOF
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

## 🔒 Security Hardening

### Network Security
```bash
# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 5000/tcp
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
chmod 600 config.json

# Run as non-root user
sudo chown -R ohms:ohms /home/ohms/OhmsAlertsReports
```

### Monitoring Security
```bash
# Restrict monitoring access
sudo ufw deny 5000/tcp
# Use SSH tunnel instead
ssh -L 5000:localhost:5000 user@server
```

## 📞 Emergency Procedures

### Service Recovery
```bash
# Emergency restart
sudo systemctl stop daily-financial-report.service
sudo systemctl start daily-financial-report.service

# Manual start if systemd fails
cd /home/ohms/OhmsAlertsReports/daily-report
source venv/bin/activate
nohup python main.py > logs/emergency.log 2>&1 &
```

### Data Recovery
```bash
# Backup configuration
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
cp config.json config.json.backup.$(date +%Y%m%d_%H%M%S)

# Restore from backup
cp .env.backup.20241224_143022 .env
```

### Complete System Reset
```bash
# Stop all services
sudo systemctl stop daily-financial-report.service
sudo systemctl stop ohms-monitoring.service
sudo docker stop signal-api

# Clear all data
rm -rf logs/* reports/* browser_sessions/* cache/*

# Restart services
sudo systemctl start daily-financial-report.service
sudo systemctl start ohms-monitoring.service
sudo docker start signal-api
```

---

**Emergency Contacts:**
- Service Status: `sudo systemctl status daily-financial-report.service`
- Manual Report: `python send_immediate_report.py`
- Health Check: `python system_health_check.py`
- Monitoring: `http://localhost:5000`

**Last Updated:** December 24, 2024  
**Version:** 2.0 (Production Ready) 