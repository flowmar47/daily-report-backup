#!/usr/bin/env python3
"""
Service Monitor for Ohms Daily Alerts
Monitors service health and sends alerts if issues detected
"""
import os
import sys
import time
import json
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
CHECK_INTERVAL = 300  # 5 minutes
ALERT_COOLDOWN = 3600  # 1 hour between alerts for same issue
LOG_FILE = "logs/monitor.log"

class ServiceMonitor:
    def __init__(self):
        self.last_alerts = {}
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration"""
        with open('config.json', 'r') as f:
            return json.load(f)
    
    def log(self, level, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        # Also write to file
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry + '\n')
    
    def check_systemd_service(self, service_name):
        """Check if systemd service is running"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() == 'active'
        except Exception as e:
            self.log('ERROR', f"Failed to check {service_name}: {e}")
            return False
    
    def check_signal_api(self):
        """Check if Signal API is responsive"""
        try:
            response = requests.get('http://localhost:8080/v1/health', timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def check_last_run(self):
        """Check when the last successful run was"""
        try:
            # Check the most recent report file
            reports_dir = Path('reports')
            if not reports_dir.exists():
                return None
                
            report_files = list(reports_dir.glob('daily_report_*.json'))
            if not report_files:
                return None
                
            # Get most recent file
            latest = max(report_files, key=lambda p: p.stat().st_mtime)
            last_modified = datetime.fromtimestamp(latest.stat().st_mtime)
            
            return last_modified
            
        except Exception as e:
            self.log('ERROR', f"Failed to check last run: {e}")
            return None
    
    def check_disk_space(self):
        """Check available disk space"""
        try:
            import shutil
            stat = shutil.disk_usage('/')
            percent_used = (stat.used / stat.total) * 100
            return percent_used < 90  # Alert if over 90% used
        except Exception:
            return True
    
    def check_log_errors(self):
        """Check for recent errors in logs"""
        try:
            log_file = Path('logs/daily_report.log')
            if not log_file.exists():
                return True
                
            # Check last 100 lines for errors
            with open(log_file, 'r') as f:
                lines = f.readlines()[-100:]
                
            error_count = sum(1 for line in lines if 'ERROR' in line or 'CRITICAL' in line)
            return error_count < 5  # Alert if more than 5 errors
            
        except Exception:
            return True
    
    def send_alert(self, issue_type, message):
        """Send alert if not recently sent"""
        # Check cooldown
        if issue_type in self.last_alerts:
            if datetime.now() - self.last_alerts[issue_type] < timedelta(seconds=ALERT_COOLDOWN):
                return
        
        # Send alert
        alert_message = f"""🚨 Service Monitor Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}

Issue: {issue_type}
{message}

Please check the service status and logs."""
        
        try:
            # Try Telegram
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            group_id = os.getenv('TELEGRAM_GROUP_ID')
            
            if bot_token and group_id:
                requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={
                        'chat_id': group_id,
                        'text': alert_message
                    }
                )
            
            # Log the alert
            self.log('ALERT', f"{issue_type}: {message}")
            self.last_alerts[issue_type] = datetime.now()
            
        except Exception as e:
            self.log('ERROR', f"Failed to send alert: {e}")
    
    def run_checks(self):
        """Run all health checks"""
        issues = []
        
        # Check main service
        if not self.check_systemd_service('daily-alerts.service'):
            issues.append(('service_down', 'Daily alerts service is not running'))
        
        # Check Signal API
        if not self.check_signal_api():
            issues.append(('signal_api_down', 'Signal API is not responding'))
        
        # Check disk space
        if not self.check_disk_space():
            issues.append(('disk_space', 'Disk space is running low (>90% used)'))
        
        # Check for errors
        if not self.check_log_errors():
            issues.append(('errors', 'Multiple errors detected in logs'))
        
        # Check last run (only during business hours)
        now = datetime.now()
        if now.hour >= 6 and now.hour <= 18:  # 6 AM to 6 PM
            last_run = self.check_last_run()
            if last_run:
                hours_since = (now - last_run).total_seconds() / 3600
                if hours_since > 24:
                    issues.append(('stale_data', f'No reports generated in {hours_since:.1f} hours'))
        
        # Send alerts for issues
        for issue_type, message in issues:
            self.send_alert(issue_type, message)
        
        # Log status
        if issues:
            self.log('WARNING', f"Health check found {len(issues)} issues")
        else:
            self.log('INFO', "Health check passed - all systems operational")
        
        return len(issues) == 0
    
    def run(self):
        """Main monitoring loop"""
        self.log('INFO', 'Service monitor starting...')
        
        while True:
            try:
                self.run_checks()
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                self.log('INFO', 'Monitor stopped by user')
                break
                
            except Exception as e:
                self.log('ERROR', f"Monitor error: {e}")
                time.sleep(60)

def main():
    """Main entry point"""
    # Load environment
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    monitor = ServiceMonitor()
    monitor.run()

if __name__ == "__main__":
    main()