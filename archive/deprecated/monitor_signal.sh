#!/bin/bash
# Monitor Signal API and ensure it stays running

# Check if service is active
if ! systemctl is-active --quiet signal-api; then
    echo "$(date): Signal API service is down, restarting..." >> /home/ohms/OhmsAlertsReports/daily-report/logs/signal-monitor.log
    sudo systemctl restart signal-api
    sleep 10
fi

# Check if API is responding
if ! curl -s http://localhost:8080/v1/about > /dev/null 2>&1; then
    echo "$(date): Signal API not responding, restarting service..." >> /home/ohms/OhmsAlertsReports/daily-report/logs/signal-monitor.log
    sudo systemctl restart signal-api
fi

# Check disk space for Docker
DOCKER_SPACE=$(df -h /var/lib/docker | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DOCKER_SPACE" -gt 90 ]; then
    echo "$(date): Docker disk space critical ($DOCKER_SPACE%), cleaning..." >> /home/ohms/OhmsAlertsReports/daily-report/logs/signal-monitor.log
    docker system prune -f
fi