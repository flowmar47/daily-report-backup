# Signal Integration Quick Reference

## 🚀 Quick Commands

### Test Report Delivery
```bash
cd /home/ohms/OhmsAlertsReports/daily-report
source venv/bin/activate
python -c "from main import run_scheduled_report; run_scheduled_report()"
```

### Check Status
```bash
# All services at once
sudo systemctl status daily-financial-report signal-api

# Signal API health
curl http://localhost:8080/v1/about

# Full status report
cd /home/ohms/OhmsAlertsReports/daily-report
python signal_status_summary.py
```

### View Logs
```bash
# Signal API logs
docker logs signal-api -f

# Report service logs
sudo journalctl -u daily-financial-report -f

# Last 50 lines
sudo journalctl -u signal-api --lines=50
```

### Restart Services
```bash
# Signal API
sudo systemctl restart signal-api

# Main report service
sudo systemctl restart daily-financial-report

# Both at once
sudo systemctl restart signal-api daily-financial-report
```

## 📱 Signal Details
- **Bot Number**: +16572463906
- **Group**: Ohms Alerts Reports
- **API**: http://localhost:8080
- **Group Link**: https://signal.group/#CjQKINt32QjJxlAbqjC22WE26xbRE9UMcUgCPttd15JxcxjPEhB2LIW5CW8UQpcceUiQ38cF

## 🔧 Troubleshooting

### Signal Not Sending?
```bash
# 1. Check if API is responding
curl http://localhost:8080/v1/about

# 2. Restart Signal API
sudo systemctl restart signal-api

# 3. Check registration
curl http://localhost:8080/v1/groups/+16572463906

# 4. View Docker logs
docker logs signal-api --tail=100
```

### Service Down?
```bash
# Check and restart
sudo systemctl status signal-api
sudo systemctl restart signal-api

# Check monitoring
tail -f /home/ohms/OhmsAlertsReports/daily-report/logs/signal_monitor.log
```

## 📊 Monitoring
- **Health Check**: Every 5 minutes
- **Auto-restart**: On failure
- **Backup**: Daily at 3 AM
- **Logs**: `/home/ohms/OhmsAlertsReports/daily-report/logs/`

## ⚡ Emergency Recovery
```bash
# If registration lost
cd /home/ohms/OhmsAlertsReports/daily-report
python register_signal_persistent.py

# Full system check
cd /home/ohms/OhmsAlertsReports
python monitor.py
```

---
Keep this handy for quick operations!