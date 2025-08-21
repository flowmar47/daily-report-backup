#!/usr/bin/env python3
"""
System Health Check Script
Monitors the financial alerts automation system and sends alerts if issues are detected.
"""

import asyncio
import subprocess
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import aiohttp
import sys
from messenger_compatibility import TelegramMessenger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def check_signal_api():
    """Check if Signal API is running and responsive."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8080/v1/health', timeout=10) as response:
                return response.status in [200, 204]
    except Exception as e:
        logger.error(f"Signal API check failed: {e}")
        return False


def check_service_status(service_name):
    """Check if a systemd service is active."""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip() == 'active'
    except Exception as e:
        logger.error(f"Service check failed for {service_name}: {e}")
        return False


def check_docker_service():
    """Check if Docker service is running."""
    try:
        result = subprocess.run(
            ['docker', 'ps', '--filter', 'name=signal-api', '--format', '{{.Status}}'],
            capture_output=True, text=True, timeout=10
        )
        return 'Up' in result.stdout
    except Exception as e:
        logger.error(f"Docker check failed: {e}")
        return False


def check_log_files():
    """Check for recent errors in log files."""
    log_dir = Path('logs')
    issues = []
    
    if log_dir.exists():
        for log_file in log_dir.glob('*.log'):
            try:
                # Check if log file was written to recently (last 24 hours)
                if log_file.stat().st_mtime > (datetime.now() - timedelta(days=1)).timestamp():
                    with open(log_file, 'r') as f:
                        recent_lines = f.readlines()[-50:]  # Last 50 lines
                        error_count = sum(1 for line in recent_lines if 'ERROR' in line or 'FAILED' in line)
                        if error_count > 5:  # More than 5 errors in recent logs
                            issues.append(f"{log_file.name}: {error_count} recent errors")
            except Exception as e:
                logger.warning(f"Could not check log file {log_file}: {e}")
    
    return issues


def check_data_freshness():
    """Check if data was collected recently."""
    latest_data_file = Path('real_alerts_only/latest_real_alerts.json')
    if latest_data_file.exists():
        try:
            with open(latest_data_file, 'r') as f:
                data = json.load(f)
                
            # Check if data has timestamp
            if 'timestamp' in data:
                # Convert ISO timestamp to datetime
                data_time = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                age_hours = (datetime.now() - data_time.replace(tzinfo=None)).total_seconds() / 3600
                
                if age_hours > 25:  # Data older than 25 hours (considering weekend gaps)
                    return f"Data is {age_hours:.1f} hours old"
            
            return None
        except Exception as e:
            return f"Could not read data file: {e}"
    else:
        return "No data file found"


async def send_health_alert(issues):
    """Send health alert to messengers."""
    try:
        from src.config.settings import settings
        
        config = settings.get_telegram_config()
        telegram = TelegramMessenger(config)
        
        alert_message = f"""🚨 SYSTEM HEALTH ALERT 🚨

⚠️ Issues detected in Financial Alerts System:

{chr(10).join(f"• {issue}" for issue in issues)}

🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🖥️ System: Daily Financial Alerts Automation

Please check the system status manually."""

        result = await telegram.send_message(alert_message)
        return result.status.name == 'SUCCESS'
        
    except Exception as e:
        logger.error(f"Failed to send health alert: {e}")
        return False


async def main():
    """Main health check function."""
    logger.info("🔍 Starting system health check...")
    
    issues = []
    
    # Check services
    if not check_service_status('signal-api.service'):
        issues.append("Signal API service is not running")
    
    if not check_service_status('daily-alerts.service'):
        issues.append("Daily Alerts service is not running")
    
    # Check Signal API directly
    if not await check_signal_api():
        issues.append("Signal API is not responding")
    
    # Check Docker container
    if not check_docker_service():
        issues.append("Signal API Docker container is not running")
    
    # Check log files for errors
    log_issues = check_log_files()
    issues.extend(log_issues)
    
    # Check data freshness
    data_issue = check_data_freshness()
    if data_issue:
        issues.append(data_issue)
    
    # Report results
    if issues:
        logger.warning(f"❌ Health check found {len(issues)} issues:")
        for issue in issues:
            logger.warning(f"  • {issue}")
        
        # Send alert if critical issues found
        critical_keywords = ['not running', 'not responding', 'container']
        has_critical = any(any(keyword in issue for keyword in critical_keywords) for issue in issues)
        
        if has_critical:
            logger.info("📨 Sending critical health alert...")
            alert_sent = await send_health_alert(issues)
            if alert_sent:
                logger.info("✅ Health alert sent successfully")
            else:
                logger.error("❌ Failed to send health alert")
        
        return False
    else:
        logger.info("✅ All health checks passed")
        return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)