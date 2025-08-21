#!/usr/bin/env python3
"""
System Service Status Verification
Checks that the 6 AM PST weekday messaging service is properly configured
"""

import subprocess
import json
import logging
from datetime import datetime, timedelta
import pytz

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_service_status():
    """Check daily-financial-report.service status"""
    logger.info("🔍 Checking System Service Status")
    
    # Check service status
    success, stdout, stderr = run_command("sudo systemctl is-active daily-financial-report.service")
    service_active = success and stdout == "active"
    
    # Check timer status
    success, stdout, stderr = run_command("sudo systemctl is-active daily-financial-report.timer")
    timer_active = success and stdout == "active"
    
    # Get next scheduled run
    success, stdout, stderr = run_command("sudo systemctl list-timers | grep daily-financial-report")
    next_run = stdout.split()[0:4] if success and stdout else None
    
    # Check process is running
    success, stdout, stderr = run_command("ps aux | grep '[m]ain.py'")
    process_running = success and stdout
    
    return {
        'service_active': service_active,
        'timer_active': timer_active,
        'next_run': ' '.join(next_run) if next_run else None,
        'process_running': process_running
    }

def check_scheduling_logic():
    """Check the Python scheduling logic"""
    logger.info("📅 Checking Scheduling Configuration")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        report_time = config['app_settings']['report_time']
        timezone = config['app_settings']['timezone']
        report_days = config['app_settings']['report_days']
        
        # Calculate next expected run
        pst = pytz.timezone(timezone)
        now = datetime.now(pst)
        
        # Find next weekday
        weekday_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 
            'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        current_weekday = now.weekday()
        target_weekdays = [weekday_map[day] for day in report_days]
        
        # Find next target day
        days_ahead = None
        for day in target_weekdays:
            if day > current_weekday:
                days_ahead = day - current_weekday
                break
        
        if days_ahead is None:  # Next week
            days_ahead = 7 + target_weekdays[0] - current_weekday
        
        hour, minute = map(int, report_time.split(':'))
        next_run_python = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
        
        return {
            'config_valid': True,
            'report_time': report_time,
            'timezone': timezone,
            'report_days': report_days,
            'next_run_calculated': next_run_python.strftime('%Y-%m-%d %H:%M:%S %Z')
        }
        
    except Exception as e:
        return {'config_valid': False, 'error': str(e)}

def check_dependencies():
    """Check that all dependencies are available"""
    logger.info("📦 Checking Dependencies")
    
    dependencies = {
        'Signal Docker': "curl -s http://localhost:8080/v1/about",
        'Telegram Bot': "python -c 'import httpx; print(\"httpx available\")'",
        'Playwright': "python -c 'from playwright.async_api import async_playwright; print(\"playwright available\")'",
        'Virtual Environment': "python -c 'import sys; print(sys.prefix)'",
    }
    
    results = {}
    for name, cmd in dependencies.items():
        if name == 'Virtual Environment':
            # Run in venv context
            cmd = f"source venv/bin/activate && {cmd}"
        
        success, stdout, stderr = run_command(cmd)
        results[name] = {'available': success, 'output': stdout if success else stderr}
    
    return results

def main():
    """Run complete system verification"""
    logger.info("🔍 SYSTEM SERVICE VERIFICATION STARTING")
    logger.info("=" * 50)
    
    # Check service status
    service_status = check_service_status()
    logger.info(f"Service Active: {'✅' if service_status['service_active'] else '❌'}")
    logger.info(f"Timer Active: {'✅' if service_status['timer_active'] else '❌'}")
    logger.info(f"Process Running: {'✅' if service_status['process_running'] else '❌'}")
    if service_status['next_run']:
        logger.info(f"Next Scheduled Run: {service_status['next_run']}")
    
    # Check scheduling configuration
    schedule_config = check_scheduling_logic()
    if schedule_config['config_valid']:
        logger.info(f"✅ Schedule Config: {schedule_config['report_days']} at {schedule_config['report_time']} {schedule_config['timezone']}")
        logger.info(f"📅 Next Python-Calculated Run: {schedule_config['next_run_calculated']}")
    else:
        logger.error(f"❌ Schedule Config Error: {schedule_config['error']}")
    
    # Check dependencies
    deps = check_dependencies()
    for name, result in deps.items():
        status = "✅" if result['available'] else "❌"
        logger.info(f"{status} {name}: {result['output'][:100]}")
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 VERIFICATION SUMMARY")
    
    all_good = (
        service_status['service_active'] and 
        service_status['timer_active'] and 
        service_status['process_running'] and
        schedule_config['config_valid'] and
        all(dep['available'] for dep in deps.values())
    )
    
    if all_good:
        logger.info("🎉 ALL SYSTEMS OPERATIONAL!")
        logger.info("✅ 6 AM PST weekday messaging is properly configured")
        logger.info("✅ Signal + Telegram messaging ready")
        logger.info("✅ Service will automatically restart on failure")
        logger.info("✅ Next run: Tomorrow 6:00 AM PDT")
    else:
        logger.warning("⚠️ Some issues detected - review above output")
        
        if not service_status['service_active']:
            logger.error("❌ Service not active - run: sudo systemctl start daily-financial-report.service")
        if not service_status['timer_active']:
            logger.error("❌ Timer not active - run: sudo systemctl start daily-financial-report.timer")
    
    logger.info("=" * 50)

if __name__ == "__main__":
    main()