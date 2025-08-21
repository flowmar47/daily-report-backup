#!/bin/bash

# Ohms Daily Alerts Service Management Script
# This script helps manage the systemd service for automated daily reports

set -e

SERVICE_NAME="daily-alerts"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PROJECT_DIR="/home/ohms/OhmsAlertsReports/daily-report"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if running as root or with sudo
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This command must be run as root or with sudo"
        exit 1
    fi
}

# Function to install the service
install_service() {
    check_root
    
    print_status "Installing Ohms Daily Alerts Service..."
    
    # Copy service file
    cp "${PROJECT_DIR}/daily-alerts.service" "$SERVICE_FILE"
    
    # Copy Signal API service if needed
    if [ -f "${PROJECT_DIR}/signal-api.service" ]; then
        cp "${PROJECT_DIR}/signal-api.service" "/etc/systemd/system/signal-api.service"
        print_status "Signal API service installed"
    fi
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable services
    systemctl enable signal-api.service
    systemctl enable ${SERVICE_NAME}.service
    
    print_status "Service installed and enabled successfully!"
    print_status "Use 'sudo $0 start' to start the service"
}

# Function to uninstall the service
uninstall_service() {
    check_root
    
    print_status "Uninstalling Ohms Daily Alerts Service..."
    
    # Stop and disable service
    systemctl stop ${SERVICE_NAME}.service || true
    systemctl disable ${SERVICE_NAME}.service || true
    
    # Remove service file
    rm -f "$SERVICE_FILE"
    
    # Reload systemd
    systemctl daemon-reload
    
    print_status "Service uninstalled successfully!"
}

# Function to start the service
start_service() {
    check_root
    
    print_status "Starting services..."
    
    # Start Signal API first
    systemctl start signal-api.service
    sleep 5
    
    # Start main service
    systemctl start ${SERVICE_NAME}.service
    
    print_status "Services started!"
    status_service
}

# Function to stop the service
stop_service() {
    check_root
    
    print_status "Stopping services..."
    systemctl stop ${SERVICE_NAME}.service
    systemctl stop signal-api.service || true
    print_status "Services stopped!"
}

# Function to restart the service
restart_service() {
    check_root
    
    print_status "Restarting services..."
    stop_service
    sleep 2
    start_service
}

# Function to check service status
status_service() {
    print_status "Checking service status..."
    echo ""
    echo "=== Signal API Service ==="
    systemctl status signal-api.service --no-pager || true
    echo ""
    echo "=== Daily Alerts Service ==="
    systemctl status ${SERVICE_NAME}.service --no-pager || true
}

# Function to view logs
view_logs() {
    print_status "Viewing service logs (press Ctrl+C to exit)..."
    journalctl -u ${SERVICE_NAME}.service -f
}

# Function to test the configuration
test_config() {
    print_status "Testing configuration..."
    
    cd "$PROJECT_DIR"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Test imports
    python3 -c "
import json
import sys
from pathlib import Path

# Test config file
with open('config.json', 'r') as f:
    config = json.load(f)
    
print('✅ Configuration file valid')
print(f'   Report time: {config[\"app_settings\"][\"report_time\"]}')
print(f'   Report days: {config[\"app_settings\"][\"report_days\"]}')

# Test environment
env_file = Path('.env')
if env_file.exists():
    print('✅ Environment file found')
else:
    print('❌ Environment file missing!')
    sys.exit(1)

# Test imports
try:
    import schedule
    import playwright
    print('✅ Required packages installed')
except ImportError as e:
    print(f'❌ Missing package: {e}')
    sys.exit(1)
    
print('\\n✅ All tests passed!')
"
}

# Function to run a test report
test_report() {
    print_status "Running test report..."
    
    cd "$PROJECT_DIR"
    source venv/bin/activate
    
    # Run immediate test
    python3 send_immediate_report.py
}

# Function to setup cron backup (in case systemd fails)
setup_cron() {
    print_status "Setting up cron backup..."
    
    # Create cron entry
    CRON_CMD="0 6 * * 1-5 cd $PROJECT_DIR && venv/bin/python main.py >> logs/cron.log 2>&1"
    
    # Add to crontab
    (crontab -l 2>/dev/null | grep -v "main.py"; echo "$CRON_CMD") | crontab -
    
    print_status "Cron backup installed (runs at 6 AM PST on weekdays)"
}

# Main menu
case "$1" in
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        status_service
        ;;
    logs)
        view_logs
        ;;
    test)
        test_config
        ;;
    test-report)
        test_report
        ;;
    setup-cron)
        setup_cron
        ;;
    *)
        echo "Ohms Daily Alerts Service Manager"
        echo ""
        echo "Usage: $0 {install|uninstall|start|stop|restart|status|logs|test|test-report|setup-cron}"
        echo ""
        echo "Commands:"
        echo "  install      - Install the systemd service"
        echo "  uninstall    - Remove the systemd service"
        echo "  start        - Start the service"
        echo "  stop         - Stop the service"
        echo "  restart      - Restart the service"
        echo "  status       - Check service status"
        echo "  logs         - View service logs (live)"
        echo "  test         - Test configuration"
        echo "  test-report  - Send a test report"
        echo "  setup-cron   - Setup cron backup (optional)"
        echo ""
        echo "Note: Most commands require sudo privileges"
        exit 1
        ;;
esac