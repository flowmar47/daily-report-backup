#!/bin/bash
# Enhanced API Signals Daily Report Wrapper Script

# Set the working directory
cd /home/ohms/OhmsAlertsReports/daily-report

# Source the virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONIOENCODING=utf-8
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Run the enhanced API signals script
python enhanced_api_signals_daily.py >> logs/enhanced_api_signals_cron.log 2>&1

# Exit with the script's exit code
exit $?
