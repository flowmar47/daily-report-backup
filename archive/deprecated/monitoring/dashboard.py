#!/usr/bin/env python3
"""
OhmsAlertsReports Monitoring Dashboard
Real-time system health monitoring and alerting
"""

import os
import sys
import json
import time
import psutil
import requests
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
from flask import Flask, render_template, jsonify, request
import threading
import schedule

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.env_config import get_env_var

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict[str, float]
    uptime: float
    load_average: List[float]

@dataclass
class ServiceStatus:
    """Service health status"""
    name: str
    status: str
    pid: Optional[int]
    memory_mb: float
    cpu_percent: float
    uptime: float
    last_log_entry: str
    error_count: int

@dataclass
class Alert:
    """System alert"""
    timestamp: datetime
    level: str
    message: str
    component: str
    resolved: bool = False

class SystemMonitor:
    """System monitoring and health checks"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.metrics_history: List[Dict] = []
        self.max_history = 1000
        
    def get_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            uptime = time.time() - psutil.boot_time()
            load_avg = psutil.getloadavg()
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                network_io={
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                uptime=uptime,
                load_average=list(load_avg)
            )
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return None
    
    def check_service_status(self, service_name: str) -> ServiceStatus:
        """Check status of a systemd service"""
        try:
            # Check systemd service status
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True
            )
            status = result.stdout.strip()
            
            # Get service PID
            pid_result = subprocess.run(
                ['systemctl', 'show', service_name, '--property=MainPID'],
                capture_output=True,
                text=True
            )
            pid_line = pid_result.stdout.strip()
            pid = int(pid_line.split('=')[1]) if '=' in pid_line else None
            
            # Get process metrics if PID exists
            memory_mb = 0
            cpu_percent = 0
            uptime = 0
            
            if pid and pid > 0:
                try:
                    process = psutil.Process(pid)
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    cpu_percent = process.cpu_percent()
                    uptime = time.time() - process.create_time()
                except psutil.NoSuchProcess:
                    pass
            
            # Get last log entry
            log_result = subprocess.run(
                ['journalctl', '-u', service_name, '-n', '1', '--no-pager'],
                capture_output=True,
                text=True
            )
            last_log = log_result.stdout.strip()
            
            # Count recent errors
            error_result = subprocess.run(
                ['journalctl', '-u', service_name, '--since', '1 hour ago', '--no-pager'],
                capture_output=True,
                text=True
            )
            error_count = error_result.stdout.lower().count('error')
            
            return ServiceStatus(
                name=service_name,
                status=status,
                pid=pid,
                memory_mb=memory_mb,
                cpu_percent=cpu_percent,
                uptime=uptime,
                last_log_entry=last_log,
                error_count=error_count
            )
        except Exception as e:
            logger.error(f"Error checking service {service_name}: {e}")
            return ServiceStatus(
                name=service_name,
                status="unknown",
                pid=None,
                memory_mb=0,
                cpu_percent=0,
                uptime=0,
                last_log_entry="Error checking service",
                error_count=0
            )
    
    def check_signal_api(self) -> Dict[str, Any]:
        """Check Signal API health"""
        try:
            response = requests.get('http://localhost:8080/v1/about', timeout=5)
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'version': response.json().get('version', 'unknown')
                }
            else:
                return {
                    'status': 'unhealthy',
                    'response_time': response.elapsed.total_seconds(),
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time': None,
                'error': str(e)
            }
    
    def check_telegram_api(self) -> Dict[str, Any]:
        """Check Telegram API health"""
        try:
            bot_token = get_env_var('TELEGRAM_BOT_TOKEN')
            if not bot_token:
                return {'status': 'unconfigured', 'error': 'No bot token found'}
            
            response = requests.get(
                f'https://api.telegram.org/bot{bot_token}/getMe',
                timeout=10
            )
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': response.elapsed.total_seconds(),
                    'bot_info': response.json().get('result', {})
                }
            else:
                return {
                    'status': 'unhealthy',
                    'response_time': response.elapsed.total_seconds(),
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'response_time': None,
                'error': str(e)
            }
    
    def check_mymama_connectivity(self) -> Dict[str, Any]:
        """Check MyMama.uk connectivity"""
        try:
            response = requests.get('https://mymama.uk', timeout=10)
            if response.status_code == 200:
                return {
                    'status': 'accessible',
                    'response_time': response.elapsed.total_seconds(),
                    'title': 'MyMama.uk'
                }
            else:
                return {
                    'status': 'unreachable',
                    'response_time': response.elapsed.total_seconds(),
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                'status': 'unreachable',
                'response_time': None,
                'error': str(e)
            }
    
    def check_log_files(self) -> Dict[str, Any]:
        """Check log file health"""
        log_dir = Path('logs')
        if not log_dir.exists():
            return {'status': 'missing', 'error': 'Logs directory not found'}
        
        log_files = {}
        for log_file in log_dir.glob('*.log'):
            try:
                stat = log_file.stat()
                size_mb = stat.st_size / 1024 / 1024
                modified = datetime.fromtimestamp(stat.st_mtime)
                
                # Check for recent activity
                recent_activity = (datetime.now() - modified) < timedelta(hours=1)
                
                log_files[log_file.name] = {
                    'size_mb': round(size_mb, 2),
                    'modified': modified.isoformat(),
                    'recent_activity': recent_activity
                }
            except Exception as e:
                log_files[log_file.name] = {'error': str(e)}
        
        return {
            'status': 'ok',
            'files': log_files,
            'total_files': len(log_files)
        }
    
    def check_disk_space(self) -> Dict[str, Any]:
        """Check disk space usage"""
        try:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / 1024 / 1024 / 1024
            total_gb = disk.total / 1024 / 1024 / 1024
            used_percent = disk.percent
            
            return {
                'free_gb': round(free_gb, 2),
                'total_gb': round(total_gb, 2),
                'used_percent': used_percent,
                'status': 'ok' if used_percent < 90 else 'warning'
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def generate_alerts(self, metrics: SystemMetrics, services: List[ServiceStatus]) -> List[Alert]:
        """Generate alerts based on current metrics"""
        alerts = []
        
        # System alerts
        if metrics.cpu_percent > 80:
            alerts.append(Alert(
                timestamp=datetime.now(),
                level='warning',
                message=f'High CPU usage: {metrics.cpu_percent:.1f}%',
                component='system'
            ))
        
        if metrics.memory_percent > 85:
            alerts.append(Alert(
                timestamp=datetime.now(),
                level='warning',
                message=f'High memory usage: {metrics.memory_percent:.1f}%',
                component='system'
            ))
        
        if metrics.disk_percent > 90:
            alerts.append(Alert(
                timestamp=datetime.now(),
                level='critical',
                message=f'Low disk space: {100 - metrics.disk_percent:.1f}% free',
                component='system'
            ))
        
        # Service alerts
        for service in services:
            if service.status != 'active':
                alerts.append(Alert(
                    timestamp=datetime.now(),
                    level='critical',
                    message=f'Service {service.name} is {service.status}',
                    component='service'
                ))
            
            if service.error_count > 5:
                alerts.append(Alert(
                    timestamp=datetime.now(),
                    level='warning',
                    message=f'Service {service.name} has {service.error_count} errors in last hour',
                    component='service'
                ))
        
        return alerts
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all system metrics and health data"""
        try:
            # System metrics
            system_metrics = self.get_system_metrics()
            
            # Service status
            services = [
                self.check_service_status('daily-financial-report.service'),
                self.check_service_status('signal-api')
            ]
            
            # API health checks
            signal_api = self.check_signal_api()
            telegram_api = self.check_telegram_api()
            mymama_connectivity = self.check_mymama_connectivity()
            
            # Log and disk checks
            log_files = self.check_log_files()
            disk_space = self.check_disk_space()
            
            # Generate alerts
            alerts = self.generate_alerts(system_metrics, services)
            self.alerts.extend(alerts)
            
            # Keep only recent alerts
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.alerts = [alert for alert in self.alerts if alert.timestamp > cutoff_time]
            
            # Store metrics history
            metrics_data = {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': system_metrics.cpu_percent,
                    'memory_percent': system_metrics.memory_percent,
                    'disk_percent': system_metrics.disk_percent,
                    'load_average': system_metrics.load_average
                },
                'services': [{
                    'name': s.name,
                    'status': s.status,
                    'memory_mb': s.memory_mb,
                    'cpu_percent': s.cpu_percent
                } for s in services]
            }
            
            self.metrics_history.append(metrics_data)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'system': system_metrics,
                'services': services,
                'apis': {
                    'signal': signal_api,
                    'telegram': telegram_api,
                    'mymama': mymama_connectivity
                },
                'logs': log_files,
                'disk': disk_space,
                'alerts': [{
                    'timestamp': alert.timestamp.isoformat(),
                    'level': alert.level,
                    'message': alert.message,
                    'component': alert.component,
                    'resolved': alert.resolved
                } for alert in self.alerts],
                'metrics_history': self.metrics_history[-50:]  # Last 50 data points
            }
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {'error': str(e)}

# Initialize Flask app
app = Flask(__name__)
monitor = SystemMonitor()

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/metrics')
def get_metrics():
    """Get current system metrics"""
    metrics = monitor.collect_all_metrics()
    return jsonify(metrics)

@app.route('/api/alerts')
def get_alerts():
    """Get current alerts"""
    return jsonify([{
        'timestamp': alert.timestamp.isoformat(),
        'level': alert.level,
        'message': alert.message,
        'component': alert.component,
        'resolved': alert.resolved
    } for alert in monitor.alerts])

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Mark an alert as resolved"""
    if 0 <= alert_id < len(monitor.alerts):
        monitor.alerts[alert_id].resolved = True
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Alert not found'}), 404

@app.route('/api/services/<service_name>/restart', methods=['POST'])
def restart_service(service_name):
    """Restart a systemd service"""
    try:
        result = subprocess.run(
            ['sudo', 'systemctl', 'restart', service_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return jsonify({'status': 'success', 'message': f'Service {service_name} restarted'})
        else:
            return jsonify({'status': 'error', 'message': result.stderr}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/logs/<service_name>')
def get_service_logs(service_name):
    """Get recent logs for a service"""
    try:
        lines = request.args.get('lines', 50, type=int)
        result = subprocess.run(
            ['journalctl', '-u', service_name, '-n', str(lines), '--no-pager'],
            capture_output=True,
            text=True
        )
        return jsonify({
            'logs': result.stdout.split('\n'),
            'error': result.stderr if result.stderr else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_metrics_collection():
    """Background metrics collection"""
    def collect_metrics():
        while True:
            try:
                monitor.collect_all_metrics()
                time.sleep(30)  # Collect every 30 seconds
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                time.sleep(60)
    
    thread = threading.Thread(target=collect_metrics, daemon=True)
    thread.start()

if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)
    
    # Start background metrics collection
    start_metrics_collection()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False) 