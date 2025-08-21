#!/bin/bash

echo "Starting system cleanup..."

# Clean APT cache
echo "Cleaning APT cache..."
sudo apt clean
sudo apt autoremove -y

# Clean playwright duplicates
echo "Removing playwright duplicates..."
rm -rf /home/ohms/.cache/ms-playwright/chromium_headless_shell-1169

# Clean Python cache
echo "Cleaning Python cache files..."
find /home/ohms/OhmsAlertsReports -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find /home/ohms/OhmsAlertsReports -name "*.pyc" -delete 2>/dev/null || true

# Clean pip cache
echo "Cleaning pip cache..."
pip cache purge 2>/dev/null || true

# Clean old log files (keep last 7 days)
echo "Cleaning old log files..."
find /home/ohms/OhmsAlertsReports -name "*.log" -mtime +7 -delete 2>/dev/null || true

# Clean temporary browser profiles
echo "Cleaning browser profiles..."
rm -rf /home/ohms/OhmsAlertsReports/daily-report/browser_sessions/* 2>/dev/null || true

# Clean docker logs if docker is running
echo "Cleaning docker logs..."
sudo docker system prune -f 2>/dev/null || true

# venv maintenance (optional - requires confirmation)
echo "Checking venv sizes..."
VENV_PATHS=(
    "/home/ohms/OhmsAlertsReports/daily-report/venv"
    "/home/ohms/OhmsAlertsReports/CurrencyInterestRates/venv"
)

TOTAL_VENV_SIZE=0
for venv_path in "${VENV_PATHS[@]}"; do
    if [[ -d "$venv_path" ]]; then
        size_kb=$(du -sk "$venv_path" 2>/dev/null | cut -f1)
        size_mb=$((size_kb / 1024))
        echo "  $(basename $(dirname $venv_path)): ${size_mb}MB"
        TOTAL_VENV_SIZE=$((TOTAL_VENV_SIZE + size_mb))
    fi
done

echo "Total venv size: ${TOTAL_VENV_SIZE}MB"

# Warn if venvs are getting large (>800MB)
if [[ $TOTAL_VENV_SIZE -gt 800 ]]; then
    echo "⚠️  venvs are large (${TOTAL_VENV_SIZE}MB). Consider running:"
    echo "   /home/ohms/OhmsAlertsReports/scripts/rebuild_venv.sh daily-report"
    echo "   /home/ohms/OhmsAlertsReports/scripts/rebuild_venv.sh currency-rates"
fi

echo "Cleanup completed!"

# Show disk usage after cleanup
echo "Disk usage after cleanup:"
df -h | grep -E "(Filesystem|/$|/tmp)"