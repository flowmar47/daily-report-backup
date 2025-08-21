#!/bin/bash

# Comprehensive Setup Script for Ohms Daily Alerts Automatic Service
# This script sets up the complete 24/7 automated reporting system

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Ohms Daily Alerts - Automatic Service Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as user ohms
if [ "$USER" != "ohms" ]; then
    echo -e "${RED}This script should be run as user 'ohms'${NC}"
    exit 1
fi

# Step 1: Environment Setup
echo -e "${YELLOW}Step 1: Setting up environment...${NC}"

# Create necessary directories
mkdir -p /home/ohms/tmp
mkdir -p /home/ohms/OhmsAlertsReports/daily-report/logs
mkdir -p /home/ohms/OhmsAlertsReports/daily-report/reports
mkdir -p /home/ohms/OhmsAlertsReports/daily-report/cache
mkdir -p /home/ohms/OhmsAlertsReports/daily-report/browser_sessions

# Make scripts executable
chmod +x manage_service.sh
chmod +x monitor_service.py
chmod +x service_runner.py

echo -e "${GREEN}✓ Environment directories created${NC}"

# Step 2: Python Dependencies
echo -e "${YELLOW}Step 2: Checking Python dependencies...${NC}"

cd /home/ohms/OhmsAlertsReports/daily-report
source venv/bin/activate

# Install/upgrade required packages
pip install --upgrade playwright schedule python-dotenv aiohttp requests

echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Step 3: Playwright Setup
echo -e "${YELLOW}Step 3: Installing Playwright browsers...${NC}"

# Set temp directory
export TMPDIR=/home/ohms/tmp
export PLAYWRIGHT_BROWSERS_PATH=/home/ohms/.cache/ms-playwright

# Install Playwright browsers
playwright install chromium

echo -e "${GREEN}✓ Playwright browsers installed${NC}"

# Step 4: Configuration Check
echo -e "${YELLOW}Step 4: Checking configuration...${NC}"

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo "Please create .env file with required credentials"
    exit 1
fi

# Test configuration
python3 -c "
import json
from pathlib import Path

# Check config.json
with open('config.json', 'r') as f:
    config = json.load(f)
    print(f'Report Time: {config[\"app_settings\"][\"report_time\"]} PST')
    print(f'Report Days: {config[\"app_settings\"][\"report_days\"]}')

# Check .env
from dotenv import load_dotenv
import os
load_dotenv('.env')

required_vars = [
    'TELEGRAM_BOT_TOKEN',
    'TELEGRAM_GROUP_ID',
    'SIGNAL_PHONE_NUMBER',
    'SIGNAL_GROUP_ID',
    'MYMAMA_USERNAME',
    'MYMAMA_PASSWORD'
]

missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    print(f'WARNING: Missing environment variables: {missing}')
else:
    print('✓ All required environment variables present')
"

echo -e "${GREEN}✓ Configuration validated${NC}"

# Step 5: Service Installation
echo -e "${YELLOW}Step 5: Installing systemd service...${NC}"

# Copy service files to systemd directory (requires sudo)
echo "Installing systemd service files (requires sudo)..."
sudo cp daily-alerts.service /etc/systemd/system/
sudo cp signal-api.service /etc/systemd/system/ 2>/dev/null || true

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable signal-api.service
sudo systemctl enable daily-alerts.service

echo -e "${GREEN}✓ Systemd services installed and enabled${NC}"

# Step 6: Start Services
echo -e "${YELLOW}Step 6: Starting services...${NC}"

# Start Signal API first
sudo systemctl start signal-api.service
sleep 5

# Start main service
sudo systemctl start daily-alerts.service

echo -e "${GREEN}✓ Services started${NC}"

# Step 7: Setup Monitoring (Optional)
echo -e "${YELLOW}Step 7: Setting up monitoring...${NC}"

# Create monitoring service
cat > monitor.service << EOF
[Unit]
Description=Ohms Daily Alerts Monitor
After=daily-alerts.service

[Service]
Type=simple
User=ohms
WorkingDirectory=/home/ohms/OhmsAlertsReports/daily-report
ExecStart=/home/ohms/OhmsAlertsReports/daily-report/venv/bin/python /home/ohms/OhmsAlertsReports/daily-report/monitor_service.py
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target
EOF

# Install monitor service (optional)
read -p "Install monitoring service? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo cp monitor.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable monitor.service
    sudo systemctl start monitor.service
    echo -e "${GREEN}✓ Monitoring service installed${NC}"
fi

# Step 8: Cron Backup (Optional)
echo -e "${YELLOW}Step 8: Setting up cron backup...${NC}"

read -p "Setup cron backup? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Add cron job for 6 AM PST weekdays
    (crontab -l 2>/dev/null | grep -v "OhmsAlertsReports/daily-report/main.py"; \
     echo "0 6 * * 1-5 cd /home/ohms/OhmsAlertsReports/daily-report && venv/bin/python main.py >> logs/cron.log 2>&1") | crontab -
    echo -e "${GREEN}✓ Cron backup installed${NC}"
fi

# Final Status Check
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Show service status
echo "Service Status:"
sudo systemctl status daily-alerts.service --no-pager | head -n 10

echo ""
echo "Next Steps:"
echo "1. Check service status: sudo systemctl status daily-alerts"
echo "2. View logs: sudo journalctl -u daily-alerts -f"
echo "3. Send test report: ./manage_service.sh test-report"
echo "4. Monitor health: ./manage_service.sh status"
echo ""
echo "The service will automatically send reports at 6:00 AM PST on weekdays."
echo "Signal and Telegram will both receive the reports."
echo ""
echo -e "${GREEN}✓ Automatic 24/7 service is now active!${NC}"