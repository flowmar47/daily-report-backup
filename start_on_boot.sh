#!/bin/bash
# Start Clean API-Based Daily Signals on Boot

cd /home/ohms/OhmsAlertsReports/daily-report
source venv/bin/activate
export PYTHONIOENCODING=utf-8
nohup python api_signals_daily.py > logs/api_signals_boot.log 2>&1 &
echo $! > api_signals_daily.pid
echo "API-based daily signals started with PID: $!"
