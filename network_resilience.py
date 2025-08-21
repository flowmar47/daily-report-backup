#!/usr/bin/env python3
"""
Network Resilience Utilities
Implements network health monitoring, connectivity checks, and resilience patterns
"""

import asyncio
import aiohttp
import logging
import time
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import socket
import subprocess
import statistics

logger = logging.getLogger(__name__)


class ConnectivityStatus(str, Enum):
    """Network connectivity status"""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    POOR = "POOR"
    OFFLINE = "OFFLINE"


class NetworkEndpoint(str, Enum):
    """Critical network endpoints to monitor"""
    GOOGLE_DNS = "8.8.8.8"
    CLOUDFLARE_DNS = "1.1.1.1"
    GOOGLE_WEB = "https://www.google.com"
    TELEGRAM_API = "https://api.telegram.org"
    MYMAMA_SITE = "https://www.mymama.uk"
    FRED_API = "https://api.stlouisfed.org"


@dataclass
class ConnectivityTest:
    """Results of a connectivity test"""
    endpoint: str
    success: bool
    response_time: float
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    status_code: Optional[int] = None


@dataclass
class NetworkHealth:
    """Overall network health assessment"""
    status: ConnectivityStatus
    response_time_avg: float
    packet_loss_rate: float
    successful_connections: int
    failed_connections: int
    last_check: datetime
    issues: List[str] = field(default_factory=list)


class CircuitBreakerState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Blocking requests
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class NetworkCircuitBreaker:
    """Circuit breaker pattern for network operations"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, 
                 success_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        
        logger.info(f"Circuit breaker initialized: failure_threshold={failure_threshold}, "
                   f"recovery_timeout={recovery_timeout}s")
    
    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit breaker: OPEN -> HALF_OPEN")
                return True
            return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self):
        """Record successful operation"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker: HALF_OPEN -> CLOSED (recovered)")
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit breaker: CLOSED -> OPEN (failures: {self.failure_count})")
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            logger.warning("Circuit breaker: HALF_OPEN -> OPEN (test failed)")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    @property
    def status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time,
            'can_execute': self.can_execute()
        }


class NetworkHealthMonitor:
    """Comprehensive network health monitoring"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.test_history: List[ConnectivityTest] = []
        self.circuit_breakers: Dict[str, NetworkCircuitBreaker] = {}
        
        # Configuration
        self.max_history = self.config.get('max_history', 100)
        self.timeout = self.config.get('timeout', 10)
        self.retry_attempts = self.config.get('retry_attempts', 3)
        self.retry_delay = self.config.get('retry_delay', 2)
        
        # Critical endpoints for monitoring
        self.endpoints = {
            'dns_primary': NetworkEndpoint.GOOGLE_DNS,
            'dns_secondary': NetworkEndpoint.CLOUDFLARE_DNS,
            'web_test': NetworkEndpoint.GOOGLE_WEB,
            'telegram_api': NetworkEndpoint.TELEGRAM_API,
            'mymama_site': NetworkEndpoint.MYMAMA_SITE,
            'fred_api': NetworkEndpoint.FRED_API
        }
        
        logger.info("Network health monitor initialized")
    
    async def check_dns_resolution(self, hostname: str = "google.com") -> ConnectivityTest:
        """Test DNS resolution"""
        start_time = time.time()
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, socket.gethostbyname, hostname)
            
            response_time = time.time() - start_time
            return ConnectivityTest(
                endpoint=f"dns://{hostname}",
                success=True,
                response_time=response_time
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return ConnectivityTest(
                endpoint=f"dns://{hostname}",
                success=False,
                response_time=response_time,
                error_message=str(e)
            )
    
    async def check_ping_connectivity(self, host: str) -> ConnectivityTest:
        """Test ping connectivity"""
        start_time = time.time()
        
        try:
            # Use ping command
            process = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', str(self.timeout), host,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            response_time = time.time() - start_time
            
            if process.returncode == 0:
                return ConnectivityTest(
                    endpoint=f"ping://{host}",
                    success=True,
                    response_time=response_time
                )
            else:
                return ConnectivityTest(
                    endpoint=f"ping://{host}",
                    success=False,
                    response_time=response_time,
                    error_message=stderr.decode() if stderr else "Ping failed"
                )
                
        except Exception as e:
            response_time = time.time() - start_time
            return ConnectivityTest(
                endpoint=f"ping://{host}",
                success=False,
                response_time=response_time,
                error_message=str(e)
            )
    
    async def check_http_connectivity(self, url: str) -> ConnectivityTest:
        """Test HTTP connectivity"""
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    response_time = time.time() - start_time
                    
                    return ConnectivityTest(
                        endpoint=url,
                        success=response.status < 400,
                        response_time=response_time,
                        status_code=response.status
                    )
                    
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return ConnectivityTest(
                endpoint=url,
                success=False,
                response_time=response_time,
                error_message="Timeout"
            )
        except Exception as e:
            response_time = time.time() - start_time
            return ConnectivityTest(
                endpoint=url,
                success=False,
                response_time=response_time,
                error_message=str(e)
            )
    
    async def run_comprehensive_connectivity_test(self) -> List[ConnectivityTest]:
        """Run comprehensive connectivity tests"""
        logger.info("Running comprehensive connectivity tests...")
        
        tests = []
        
        # DNS tests
        dns_test = await self.check_dns_resolution()
        tests.append(dns_test)
        
        # Ping tests
        for name, endpoint in [('google_dns', NetworkEndpoint.GOOGLE_DNS), 
                              ('cloudflare_dns', NetworkEndpoint.CLOUDFLARE_DNS)]:
            ping_test = await self.check_ping_connectivity(endpoint)
            tests.append(ping_test)
        
        # HTTP tests
        for name, endpoint in [('google_web', NetworkEndpoint.GOOGLE_WEB),
                              ('telegram_api', NetworkEndpoint.TELEGRAM_API),
                              ('mymama_site', NetworkEndpoint.MYMAMA_SITE)]:
            http_test = await self.check_http_connectivity(endpoint)
            tests.append(http_test)
        
        # Store results
        self.test_history.extend(tests)
        
        # Maintain history limit
        if len(self.test_history) > self.max_history:
            self.test_history = self.test_history[-self.max_history:]
        
        return tests
    
    def assess_network_health(self, recent_tests: Optional[List[ConnectivityTest]] = None) -> NetworkHealth:
        """Assess overall network health"""
        if recent_tests is None:
            # Use last 10 tests from history
            recent_tests = self.test_history[-10:] if self.test_history else []
        
        if not recent_tests:
            return NetworkHealth(
                status=ConnectivityStatus.OFFLINE,
                response_time_avg=0,
                packet_loss_rate=1.0,
                successful_connections=0,
                failed_connections=0,
                last_check=datetime.now(),
                issues=["No connectivity tests available"]
            )
        
        # Calculate metrics
        successful = [t for t in recent_tests if t.success]
        failed = [t for t in recent_tests if not t.success]
        
        successful_count = len(successful)
        failed_count = len(failed)
        total_count = len(recent_tests)
        
        packet_loss_rate = failed_count / total_count if total_count > 0 else 1.0
        
        if successful:
            avg_response_time = statistics.mean([t.response_time for t in successful])
        else:
            avg_response_time = float('inf')
        
        # Determine status
        issues = []
        
        if packet_loss_rate >= 0.8:
            status = ConnectivityStatus.OFFLINE
            issues.append("High packet loss (>80%)")
        elif packet_loss_rate >= 0.5:
            status = ConnectivityStatus.POOR
            issues.append("Poor connectivity (>50% packet loss)")
        elif packet_loss_rate >= 0.2:
            status = ConnectivityStatus.DEGRADED
            issues.append("Degraded connectivity (>20% packet loss)")
        elif avg_response_time > 5.0:
            status = ConnectivityStatus.DEGRADED
            issues.append("High latency (>5s average)")
        else:
            status = ConnectivityStatus.HEALTHY
        
        # Check specific endpoints
        telegram_tests = [t for t in recent_tests if 'telegram' in t.endpoint.lower()]
        if telegram_tests and all(not t.success for t in telegram_tests):
            issues.append("Telegram API unreachable")
        
        mymama_tests = [t for t in recent_tests if 'mymama' in t.endpoint.lower()]
        if mymama_tests and all(not t.success for t in mymama_tests):
            issues.append("MyMama site unreachable")
        
        return NetworkHealth(
            status=status,
            response_time_avg=avg_response_time,
            packet_loss_rate=packet_loss_rate,
            successful_connections=successful_count,
            failed_connections=failed_count,
            last_check=datetime.now(),
            issues=issues
        )
    
    def get_circuit_breaker(self, endpoint: str) -> NetworkCircuitBreaker:
        """Get or create circuit breaker for endpoint"""
        if endpoint not in self.circuit_breakers:
            self.circuit_breakers[endpoint] = NetworkCircuitBreaker()
        return self.circuit_breakers[endpoint]
    
    async def execute_with_circuit_breaker(self, endpoint: str, operation):
        """Execute operation with circuit breaker protection"""
        breaker = self.get_circuit_breaker(endpoint)
        
        if not breaker.can_execute():
            raise Exception(f"Circuit breaker OPEN for {endpoint}")
        
        try:
            result = await operation()
            breaker.record_success()
            return result
        except Exception as e:
            breaker.record_failure()
            raise e
    
    async def resilient_http_request(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make HTTP request with resilience patterns"""
        breaker = self.get_circuit_breaker(url)
        
        if not breaker.can_execute():
            raise Exception(f"Circuit breaker OPEN for {url}")
        
        for attempt in range(self.retry_attempts):
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, **kwargs) as response:
                        if response.status < 500:  # Don't retry client errors
                            breaker.record_success()
                            return response
                        else:
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status
                            )
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    breaker.record_failure()
                    raise e
                else:
                    logger.warning(f"HTTP request attempt {attempt + 1} failed for {url}: {e}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        breaker.record_failure()
        raise Exception(f"All {self.retry_attempts} attempts failed for {url}")
    
    def get_network_statistics(self) -> Dict[str, Any]:
        """Get comprehensive network statistics"""
        recent_tests = self.test_history[-50:] if self.test_history else []
        health = self.assess_network_health(recent_tests)
        
        # Circuit breaker statuses
        breaker_status = {}
        for endpoint, breaker in self.circuit_breakers.items():
            breaker_status[endpoint] = breaker.status
        
        # Endpoint-specific statistics
        endpoint_stats = {}
        for endpoint in [e.value for e in NetworkEndpoint]:
            endpoint_tests = [t for t in recent_tests if endpoint in t.endpoint]
            if endpoint_tests:
                successful = [t for t in endpoint_tests if t.success]
                endpoint_stats[endpoint] = {
                    'success_rate': len(successful) / len(endpoint_tests),
                    'avg_response_time': statistics.mean([t.response_time for t in successful]) if successful else None,
                    'total_tests': len(endpoint_tests),
                    'last_test': max(endpoint_tests, key=lambda x: x.timestamp).timestamp.isoformat()
                }
        
        return {
            'overall_health': {
                'status': health.status.value,
                'packet_loss_rate': health.packet_loss_rate,
                'avg_response_time': health.response_time_avg,
                'issues': health.issues
            },
            'circuit_breakers': breaker_status,
            'endpoint_statistics': endpoint_stats,
            'test_history_size': len(self.test_history),
            'last_assessment': health.last_check.isoformat()
        }
    
    async def run_continuous_monitoring(self, interval: int = 300):
        """Run continuous network monitoring"""
        logger.info(f"Starting continuous network monitoring (interval: {interval}s)")
        
        while True:
            try:
                tests = await self.run_comprehensive_connectivity_test()
                health = self.assess_network_health(tests)
                
                logger.info(f"Network health: {health.status.value} "
                           f"(loss: {health.packet_loss_rate:.1%}, "
                           f"latency: {health.response_time_avg:.2f}s)")
                
                if health.issues:
                    logger.warning(f"Network issues: {', '.join(health.issues)}")
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Network monitoring error: {e}")
                await asyncio.sleep(60)  # Shorter retry on error


# Global network monitor instance
network_monitor = NetworkHealthMonitor()


async def main():
    """Test network resilience utilities"""
    print("🌐 Testing Network Resilience Utilities...")
    
    # Run comprehensive connectivity test
    print("\n📡 Running connectivity tests...")
    tests = await network_monitor.run_comprehensive_connectivity_test()
    
    for test in tests:
        status = "✅" if test.success else "❌"
        print(f"{status} {test.endpoint}: {test.response_time:.3f}s")
        if test.error_message:
            print(f"   Error: {test.error_message}")
    
    # Assess network health
    print("\n🏥 Network health assessment...")
    health = network_monitor.assess_network_health(tests)
    print(f"Status: {health.status.value}")
    print(f"Packet Loss: {health.packet_loss_rate:.1%}")
    print(f"Avg Response Time: {health.response_time_avg:.3f}s")
    if health.issues:
        print(f"Issues: {', '.join(health.issues)}")
    
    # Test circuit breaker
    print("\n🔌 Testing circuit breaker...")
    breaker = network_monitor.get_circuit_breaker("test_endpoint")
    print(f"Initial state: {breaker.state.value}")
    
    # Simulate failures
    for i in range(6):
        breaker.record_failure()
        print(f"After failure {i+1}: {breaker.state.value}")
    
    # Test recovery
    await asyncio.sleep(1)  # Brief pause
    if breaker.can_execute():
        breaker.record_success()
        breaker.record_success()
        breaker.record_success()
        print(f"After recovery: {breaker.state.value}")
    
    # Get statistics
    print("\n📊 Network statistics...")
    stats = network_monitor.get_network_statistics()
    print(json.dumps(stats, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())