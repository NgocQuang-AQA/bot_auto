#!/usr/bin/env python3
"""
Bot Slack Service Monitoring

This module provides comprehensive monitoring capabilities for the Bot Slack service,
including health checks, performance metrics, alerting, and logging analysis.
"""

# Setup project path
from utils.common import setup_project_path, setup_logging, handle_exceptions
setup_project_path()

from config.settings import Config
from constants import DEFAULT_PORT, DEFAULT_HOST

import time
import psutil
import requests
import json
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional
import threading
import os
from dataclasses import dataclass

logger = setup_logging(__name__)

@dataclass
class HealthStatus:
    """Health status data structure"""
    is_healthy: bool
    response_time: float
    status_code: int
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class SystemMetrics:
    """System metrics data structure"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict
    process_count: int
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.alert_history = []
        self.last_alert_time = {}
        
    def send_email_alert(self, subject: str, message: str, severity: str = 'WARNING'):
        """Send email alert"""
        try:
            if not self.config.get('email', {}).get('enabled', False):
                return
                
            smtp_config = self.config['email']
            
            msg = MimeMultipart()
            msg['From'] = smtp_config['from']
            msg['To'] = ', '.join(smtp_config['to'])
            msg['Subject'] = f"[{severity}] Bot Slack Service - {subject}"
            
            body = f"""
            Alert Details:
            Severity: {severity}
            Time: {datetime.now().isoformat()}
            Service: Bot Slack Service
            
            Message:
            {message}
            
            --
            Bot Slack Monitoring System
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
            if smtp_config.get('use_tls', True):
                server.starttls()
            if smtp_config.get('username') and smtp_config.get('password'):
                server.login(smtp_config['username'], smtp_config['password'])
            
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Email alert sent: {subject}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    def send_slack_alert(self, message: str, severity: str = 'WARNING'):
        """Send Slack alert"""
        try:
            if not self.config.get('slack', {}).get('enabled', False):
                return
                
            slack_config = self.config['slack']
            webhook_url = slack_config['webhook_url']
            
            color_map = {
                'INFO': '#36a64f',
                'WARNING': '#ff9500',
                'ERROR': '#ff0000',
                'CRITICAL': '#8B0000'
            }
            
            payload = {
                'attachments': [{
                    'color': color_map.get(severity, '#ff9500'),
                    'title': f'Bot Slack Service Alert - {severity}',
                    'text': message,
                    'footer': 'Bot Slack Monitoring',
                    'ts': int(time.time())
                }]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.info(f"Slack alert sent: {severity}")
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
    
    def should_send_alert(self, alert_type: str, cooldown_minutes: int = 30) -> bool:
        """Check if alert should be sent based on cooldown period"""
        now = datetime.now()
        last_alert = self.last_alert_time.get(alert_type)
        
        if last_alert is None:
            self.last_alert_time[alert_type] = now
            return True
            
        if now - last_alert > timedelta(minutes=cooldown_minutes):
            self.last_alert_time[alert_type] = now
            return True
            
        return False
    
    def send_alert(self, alert_type: str, message: str, severity: str = 'WARNING'):
        """Send alert through configured channels"""
        if not self.should_send_alert(alert_type):
            return
            
        self.alert_history.append({
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now()
        })
        
        # Send through configured channels
        if self.config.get('email', {}).get('enabled', False):
            self.send_email_alert(alert_type, message, severity)
            
        if self.config.get('slack', {}).get('enabled', False):
            self.send_slack_alert(message, severity)

class HealthChecker:
    """Performs health checks on the service"""
    
    def __init__(self, base_url: str = f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"):
        self.base_url = base_url
    
    @handle_exceptions(default_return=HealthStatus(False, 0.0, 0, "Health check failed due to unexpected error"))
    def check_health_endpoint(self) -> HealthStatus:
        """Check the health endpoint"""
        start_time = time.time()
        
        response = requests.get(f'{self.base_url}/health', timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                return HealthStatus(
                    is_healthy=True,
                    response_time=response_time,
                    status_code=response.status_code
                )
            else:
                return HealthStatus(
                    is_healthy=False,
                    response_time=response_time,
                    status_code=response.status_code,
                    error_message=f"Service reports unhealthy: {data.get('error', 'Unknown')}"
                )
        else:
            return HealthStatus(
                is_healthy=False,
                response_time=response_time,
                status_code=response.status_code,
                error_message=f"HTTP {response.status_code}"
            )
    
    def check_endpoints(self) -> Dict[str, HealthStatus]:
        """Check multiple endpoints"""
        endpoints = ['/health', '/metrics']
        results = {}
        
        for endpoint in endpoints:
            start_time = time.time()
            try:
                response = requests.get(f'{self.base_url}{endpoint}', timeout=5)
                response_time = time.time() - start_time
                
                results[endpoint] = HealthStatus(
                    is_healthy=response.status_code == 200,
                    response_time=response_time,
                    status_code=response.status_code,
                    error_message=None if response.status_code == 200 else f"HTTP {response.status_code}"
                )
            except Exception as e:
                results[endpoint] = HealthStatus(
                    is_healthy=False,
                    response_time=time.time() - start_time,
                    status_code=0,
                    error_message=str(e)
                )
        
        return results

class SystemMonitor:
    """Monitors system resources"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @handle_exceptions(default_return=SystemMetrics(
        cpu_percent=0.0,
        memory_percent=0.0,
        disk_percent=0.0,
        network_io={},
        process_count=0
    ))
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        # Get network I/O stats
        net_io = psutil.net_io_counters()
        network_io = {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }
        
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_percent=psutil.virtual_memory().percent,
            disk_percent=psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
            network_io=network_io,
            process_count=len(psutil.pids())
        )
    
    def check_resource_thresholds(self, metrics: SystemMetrics, thresholds: Dict) -> List[str]:
        """Check if metrics exceed thresholds"""
        alerts = []
        
        if metrics.cpu_percent > thresholds.get('cpu_percent', 80):
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
            
        if metrics.memory_percent > thresholds.get('memory_percent', 80):
            alerts.append(f"High memory usage: {metrics.memory_percent:.1f}%")
            
        if metrics.disk_percent > thresholds.get('disk_percent', 85):
            alerts.append(f"High disk usage: {metrics.disk_percent:.1f}%")
        
        return alerts

class LogAnalyzer:
    """Analyzes application logs for issues"""
    
    def __init__(self, log_file: str = 'logs/app.log'):
        self.log_file = log_file
        self.logger = logging.getLogger(__name__)
    
    def analyze_recent_logs(self, minutes: int = 10) -> Dict:
        """Analyze logs from the last N minutes"""
        try:
            if not os.path.exists(self.log_file):
                return {'error': 'Log file not found'}
            
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            error_count = 0
            warning_count = 0
            recent_errors = []
            
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        # Simple log parsing - adjust based on your log format
                        if 'ERROR' in line:
                            error_count += 1
                            if len(recent_errors) < 5:  # Keep last 5 errors
                                recent_errors.append(line.strip())
                        elif 'WARNING' in line:
                            warning_count += 1
                    except Exception:
                        continue
            
            return {
                'error_count': error_count,
                'warning_count': warning_count,
                'recent_errors': recent_errors,
                'analysis_period_minutes': minutes
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing logs: {e}")
            return {'error': str(e)}

class ServiceMonitor:
    """Main monitoring service"""
    
    def __init__(self, config_file: str = 'monitoring_config.json'):
        self.config = self.load_config(config_file)
        self.health_checker = HealthChecker(self.config.get('service_url', 'http://localhost:5000'))
        self.system_monitor = SystemMonitor()
        self.log_analyzer = LogAnalyzer(self.config.get('log_file', 'logs/app.log'))
        self.alert_manager = AlertManager(self.config.get('alerts', {}))
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.monitor_thread = None
    
    def load_config(self, config_file: str) -> Dict:
        """Load monitoring configuration"""
        default_config = {
            'service_url': 'http://localhost:5000',
            'log_file': 'logs/app.log',
            'check_interval': 60,
            'thresholds': {
                'cpu_percent': 80,
                'memory_percent': 80,
                'disk_percent': 85,
                'response_time': 5.0
            },
            'alerts': {
                'email': {
                    'enabled': False,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'use_tls': True,
                    'from': 'alerts@yourcompany.com',
                    'to': ['admin@yourcompany.com'],
                    'username': '',
                    'password': ''
                },
                'slack': {
                    'enabled': False,
                    'webhook_url': ''
                }
            }
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
            print("Using default configuration")
        
        return default_config
    
    def perform_health_check(self) -> Dict:
        """Perform comprehensive health check"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'overall_healthy': True,
            'checks': {}
        }
        
        # Check main health endpoint
        health_status = self.health_checker.check_health_endpoint()
        results['checks']['health_endpoint'] = {
            'healthy': health_status.is_healthy,
            'response_time': health_status.response_time,
            'status_code': health_status.status_code,
            'error': health_status.error_message
        }
        
        if not health_status.is_healthy:
            results['overall_healthy'] = False
            self.alert_manager.send_alert(
                'service_down',
                f"Service health check failed: {health_status.error_message}",
                'CRITICAL'
            )
        
        # Check response time
        if health_status.response_time > self.config['thresholds']['response_time']:
            self.alert_manager.send_alert(
                'slow_response',
                f"Slow response time: {health_status.response_time:.2f}s",
                'WARNING'
            )
        
        # Check system metrics
        try:
            metrics = self.system_monitor.get_system_metrics()
            results['checks']['system_metrics'] = {
                'cpu_percent': metrics.cpu_percent,
                'memory_percent': metrics.memory_percent,
                'disk_percent': metrics.disk_percent,
                'process_count': metrics.process_count
            }
            
            # Check thresholds
            threshold_alerts = self.system_monitor.check_resource_thresholds(
                metrics, self.config['thresholds']
            )
            
            for alert in threshold_alerts:
                self.alert_manager.send_alert('resource_threshold', alert, 'WARNING')
                
        except Exception as e:
            results['checks']['system_metrics'] = {'error': str(e)}
            results['overall_healthy'] = False
        
        # Analyze logs
        log_analysis = self.log_analyzer.analyze_recent_logs()
        results['checks']['log_analysis'] = log_analysis
        
        if log_analysis.get('error_count', 0) > 10:  # More than 10 errors in last 10 minutes
            self.alert_manager.send_alert(
                'high_error_rate',
                f"High error rate: {log_analysis['error_count']} errors in last 10 minutes",
                'WARNING'
            )
        
        return results
    
    def monitor_loop(self):
        """Main monitoring loop"""
        self.logger.info("Starting monitoring loop")
        
        while self.running:
            try:
                results = self.perform_health_check()
                
                # Log results
                if results['overall_healthy']:
                    self.logger.info("Health check passed")
                else:
                    self.logger.warning(f"Health check failed: {results}")
                
                # Save results to file
                self.save_monitoring_results(results)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                self.alert_manager.send_alert(
                    'monitoring_error',
                    f"Monitoring system error: {e}",
                    'ERROR'
                )
            
            # Wait for next check
            time.sleep(self.config['check_interval'])
    
    def save_monitoring_results(self, results: Dict):
        """Save monitoring results to file"""
        try:
            os.makedirs('monitoring', exist_ok=True)
            filename = f"monitoring/health_check_{datetime.now().strftime('%Y%m%d')}.json"
            
            # Append to daily file
            with open(filename, 'a') as f:
                f.write(json.dumps(results) + '\n')
                
        except Exception as e:
            self.logger.error(f"Error saving monitoring results: {e}")
    
    def start(self):
        """Start monitoring"""
        if self.running:
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        self.logger.info("Monitoring started")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        self.logger.info("Monitoring stopped")
    
    def get_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            'running': self.running,
            'config': self.config,
            'last_check': self.perform_health_check()
        }

def main():
    """Main function for standalone monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bot Slack Service Monitor')
    parser.add_argument('--config', default='monitoring_config.json', help='Configuration file')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('monitoring/monitor.log'),
            logging.StreamHandler()
        ]
    )
    
    monitor = ServiceMonitor(args.config)
    
    if args.once:
        # Run once and print results
        results = monitor.perform_health_check()
        print(json.dumps(results, indent=2))
    elif args.daemon:
        # Run as daemon
        try:
            monitor.start()
            print("Monitoring started. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping monitor...")
            monitor.stop()
    else:
        # Interactive mode
        monitor.start()
        try:
            while True:
                command = input("\nEnter command (status/stop/quit): ").strip().lower()
                if command == 'status':
                    status = monitor.get_status()
                    print(json.dumps(status, indent=2, default=str))
                elif command in ['stop', 'quit']:
                    break
        except KeyboardInterrupt:
            pass
        finally:
            monitor.stop()

if __name__ == '__main__':
    main()