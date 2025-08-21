#!/bin/bash
#
# Setup cron job for daily financial alerts
# Runs Monday-Friday at 6:00 AM PST
#

echo "📅 Setting up cron job for daily financial alerts..."

# Get the absolute path to the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH="${SCRIPT_DIR}/venv/bin/python"
MAIN_SCRIPT="${SCRIPT_DIR}/main.py"
LOG_FILE="${SCRIPT_DIR}/logs/daily_report_cron.log"

# Create logs directory if it doesn't exist
mkdir -p "${SCRIPT_DIR}/logs"

# Create a wrapper script for cron
cat > "${SCRIPT_DIR}/run_daily_report.sh" << 'EOF'
#!/bin/bash
# Daily Report Cron Wrapper Script

# Set the working directory
cd /home/ohms/OhmsAlertsReports/daily-report

# Source the virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONIOENCODING=utf-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Run the main script
python main.py >> logs/daily_report_cron.log 2>&1

# Exit with the script's exit code
exit $?
EOF

# Make the wrapper script executable
chmod +x "${SCRIPT_DIR}/run_daily_report.sh"

# Create systemd service for better reliability
cat > /tmp/daily-financial-report.service << EOF
[Unit]
Description=Daily Financial Report Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=${SCRIPT_DIR}
ExecStart=${SCRIPT_DIR}/run_daily_report.sh
Restart=always
RestartSec=300
StandardOutput=append:${LOG_FILE}
StandardError=append:${LOG_FILE}

[Install]
WantedBy=multi-user.target
EOF

# Create systemd timer for scheduling
cat > /tmp/daily-financial-report.timer << EOF
[Unit]
Description=Daily Financial Report Timer
Requires=daily-financial-report.service

[Timer]
# Run Monday through Friday at 6:00 AM PST
OnCalendar=Mon-Fri *-*-* 06:00:00 America/Los_Angeles
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Check if running as root for systemd installation
if [ "$EUID" -eq 0 ]; then
    echo "🔧 Installing systemd service and timer..."
    cp /tmp/daily-financial-report.service /etc/systemd/system/
    cp /tmp/daily-financial-report.timer /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable daily-financial-report.timer
    systemctl start daily-financial-report.timer
    echo "✅ Systemd timer installed and started"
else
    echo "⚠️  Not running as root. Setting up user cron job instead..."
    
    # Create cron job entry
    CRON_CMD="${SCRIPT_DIR}/run_daily_report.sh"
    CRON_JOB="0 6 * * 1-5 $CRON_CMD"
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "$MAIN_SCRIPT"; then
        echo "⚠️  Cron job already exists. Updating..."
        # Remove old cron job
        crontab -l 2>/dev/null | grep -v "$MAIN_SCRIPT" | crontab -
    fi
    
    # Add new cron job
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ Cron job installed for user $USER"
fi

# Create startup script for reboot persistence
cat > "${SCRIPT_DIR}/start_on_boot.sh" << 'EOF'
#!/bin/bash
# Start Daily Report on Boot

cd /home/ohms/OhmsAlertsReports/daily-report
source venv/bin/activate
nohup python main.py > logs/main_boot.log 2>&1 &
echo $! > daily_report.pid
echo "Daily report started with PID: $!"
EOF

chmod +x "${SCRIPT_DIR}/start_on_boot.sh"

# Add to user's crontab for boot persistence
BOOT_CMD="${SCRIPT_DIR}/start_on_boot.sh"
BOOT_JOB="@reboot sleep 60 && $BOOT_CMD"

if ! crontab -l 2>/dev/null | grep -q "@reboot.*start_on_boot.sh"; then
    (crontab -l 2>/dev/null; echo "$BOOT_JOB") | crontab -
    echo "✅ Boot persistence added to crontab"
fi

echo ""
echo "📋 SCHEDULING SUMMARY:"
echo "✅ Daily reports scheduled for Monday-Friday at 6:00 AM PST"
echo "✅ Logs will be written to: ${LOG_FILE}"
echo "✅ System will restart automatically after reboot"
echo ""
echo "🔍 To check the schedule:"
echo "   crontab -l                    # View user cron jobs"
echo "   systemctl status daily-financial-report.timer  # If using systemd"
echo ""
echo "📊 To run manually:"
echo "   ${SCRIPT_DIR}/run_daily_report.sh"
echo ""
echo "✅ Setup complete!"