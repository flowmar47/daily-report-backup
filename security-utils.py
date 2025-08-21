"""
Enhanced security utilities for web scraping
"""

import os
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
import requests
from fake_useragent import UserAgent
import random
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import hashlib

logger = logging.getLogger(__name__)

class ProxyManager:
    """Manage proxy rotation for enhanced anonymity"""
    
    def __init__(self, config: dict):
        self.config = config
        self.proxies = []
        self.current_proxy_index = 0
        self.proxy_stats = {}
        
    def load_proxies(self, proxy_file: str = None):
        """Load proxies from file or provider"""
        if proxy_file and Path(proxy_file).exists():
            with open(proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            logger.info(f"Loaded {len(self.proxies)} proxies")
        else:
            # Could integrate with proxy providers like Bright Data, ZenRows
            logger.warning("No proxy file found, running without proxies")
    
    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        
        # Track proxy usage
        if proxy not in self.proxy_stats:
            self.proxy_stats[proxy] = {
                'uses': 0,
                'failures': 0,
                'last_used': None
            }
        
        self.proxy_stats[proxy]['uses'] += 1
        self.proxy_stats[proxy]['last_used'] = datetime.now()
        
        return {
            'http': proxy,
            'https': proxy
        }
    
    def mark_proxy_failed(self, proxy: str):
        """Mark a proxy as failed"""
        if proxy in self.proxy_stats:
            self.proxy_stats[proxy]['failures'] += 1
            
            # Remove proxy if too many failures
            if self.proxy_stats[proxy]['failures'] > 3:
                logger.warning(f"Removing failed proxy: {proxy}")
                self.proxies.remove(proxy)


class HeaderManager:
    """Manage dynamic header generation"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.referers = [
            'https://www.google.com/',
            'https://www.bing.com/',
            'https://duckduckgo.com/',
            'https://www.yahoo.com/'
        ]
        
    def get_headers(self, url: str = None) -> dict:
        """Generate realistic headers"""
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        # Add referer
        if url:
            headers['Referer'] = random.choice(self.referers)
        
        # Randomize some headers
        if random.random() > 0.5:
            headers['X-Forwarded-For'] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        
        return headers


class SessionManager:
    """Manage browser sessions with rotation"""
    
    def __init__(self, max_uses: int = 10):
        self.max_uses = max_uses
        self.session_uses = 0
        self.session_created = datetime.now()
        self.session_id = self._generate_session_id()
        
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return hashlib.md5(f"{datetime.now().isoformat()}{random.random()}".encode()).hexdigest()
    
    def should_rotate(self) -> bool:
        """Check if session should be rotated"""
        # Rotate based on usage count
        if self.session_uses >= self.max_uses:
            logger.info(f"Session rotation needed: {self.session_uses} uses")
            return True
        
        # Rotate based on age (1 hour)
        session_age = datetime.now() - self.session_created
        if session_age > timedelta(hours=1):
            logger.info(f"Session rotation needed: {session_age} old")
            return True
        
        return False
    
    def increment_usage(self):
        """Increment session usage counter"""
        self.session_uses += 1
    
    def reset(self):
        """Reset session tracking"""
        self.session_uses = 0
        self.session_created = datetime.now()
        self.session_id = self._generate_session_id()
        logger.info(f"Session reset: {self.session_id}")


class CAPTCHAHandler:
    """Handle CAPTCHA detection and solving"""
    
    def __init__(self, solver_service: str = None, api_key: str = None):
        self.solver_service = solver_service  # e.g., '2captcha', 'anticaptcha'
        self.api_key = api_key
        
    async def detect_captcha(self, page) -> bool:
        """Detect if CAPTCHA is present"""
        captcha_indicators = [
            'iframe[src*="recaptcha"]',
            'div[class*="captcha"]',
            'div[id*="captcha"]',
            'img[src*="captcha"]',
            '.g-recaptcha',
            '#recaptcha'
        ]
        
        for indicator in captcha_indicators:
            if await page.locator(indicator).count() > 0:
                logger.warning("CAPTCHA detected")
                return True
        
        return False
    
    async def solve_captcha(self, page, captcha_type: str = 'recaptcha'):
        """Attempt to solve CAPTCHA"""
        if not self.solver_service or not self.api_key:
            logger.error("CAPTCHA solver not configured")
            return False
        
        # This would integrate with services like 2Captcha
        # For now, just log and return
        logger.info(f"Would solve {captcha_type} using {self.solver_service}")
        return False


class DataSanitizer:
    """Sanitize and anonymize scraped data"""
    
    @staticmethod
    def remove_pii(text: str) -> str:
        """Remove personally identifiable information"""
        import re
        
        # Email addresses
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]', text)
        
        # Phone numbers (various formats)
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
            r'\b\d{10,11}\b',  # Simple number string
            r'\+\d{1,3}\s?\d{1,4}\s?\d{1,4}\s?\d{1,4}',  # International
        ]
        for pattern in phone_patterns:
            text = re.sub(pattern, '[PHONE]', text)
        
        # Credit card numbers
        text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CC]', text)
        
        # Social Security Numbers
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        # IP addresses
        text = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP]', text)
        
        return text
    
    @staticmethod
    def anonymize_urls(text: str) -> str:
        """Anonymize URLs in text"""
        import re
        
        # Keep domain but remove specific paths
        def replace_url(match):
            url = match.group(0)
            if 'mymama.uk' in url.lower():
                return 'https://mymama.uk/[PATH]'
            return '[URL]'
        
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.sub(url_pattern, replace_url, text)


class RateLimiter:
    """Implement rate limiting for requests with adaptive delays"""
    
    def __init__(self, min_delay: float = 3.0, max_delay: float = 10.0):
        self.request_times = {}
        self.min_interval = min_delay
        self.max_interval = max_delay
        self.failure_counts = {}
        self.adaptive_delays = {}
        
    def can_request(self, domain: str) -> bool:
        """Check if we can make a request to domain"""
        now = datetime.now()
        
        if domain not in self.request_times:
            self.request_times[domain] = now
            return True
        
        time_since_last = (now - self.request_times[domain]).total_seconds()
        
        if time_since_last >= self.min_interval:
            self.request_times[domain] = now
            return True
        
        return False
    
    def wait_time(self, domain: str) -> float:
        """Get time to wait before next request with adaptive delays"""
        if domain not in self.request_times:
            return 0
        
        time_since_last = (datetime.now() - self.request_times[domain]).total_seconds()
        
        # Get adaptive delay for this domain
        adaptive_delay = self.adaptive_delays.get(domain, self.min_interval)
        wait = max(0, adaptive_delay - time_since_last)
        
        # Add random jitter
        return wait + random.uniform(0.5, 1.5)
    
    def get_delay(self, domain: str = 'default') -> float:
        """Get appropriate delay for domain"""
        return self.wait_time(domain)
    
    def record_failure(self, domain: str):
        """Record a failure for adaptive rate limiting"""
        self.failure_counts[domain] = self.failure_counts.get(domain, 0) + 1
        
        # Increase delay for domains with failures
        if self.failure_counts[domain] > 3:
            current_delay = self.adaptive_delays.get(domain, self.min_interval)
            new_delay = min(current_delay * 1.5, self.max_interval)
            self.adaptive_delays[domain] = new_delay
            logger.warning(f"Increased delay for {domain} to {new_delay}s due to failures")
    
    def record_success(self, domain: str):
        """Record a success for adaptive rate limiting"""
        if domain in self.failure_counts:
            # Gradually reduce failure count
            self.failure_counts[domain] = max(0, self.failure_counts[domain] - 1)
            
            # Reset delay if no recent failures
            if self.failure_counts[domain] == 0 and domain in self.adaptive_delays:
                del self.adaptive_delays[domain]


class SuccessRateTracker:
    """Track scraping success rates"""
    
    def __init__(self):
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'blocked_requests': 0,
            'captcha_encounters': 0
        }
        self.domain_stats = {}
        
    def record_request(self, domain: str, success: bool, blocked: bool = False, captcha: bool = False):
        """Record request outcome"""
        self.stats['total_requests'] += 1
        
        if success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
            
        if blocked:
            self.stats['blocked_requests'] += 1
            
        if captcha:
            self.stats['captcha_encounters'] += 1
        
        # Track per domain
        if domain not in self.domain_stats:
            self.domain_stats[domain] = {
                'total': 0,
                'success': 0,
                'blocked': 0
            }
        
        self.domain_stats[domain]['total'] += 1
        if success:
            self.domain_stats[domain]['success'] += 1
        if blocked:
            self.domain_stats[domain]['blocked'] += 1
    
    def get_success_rate(self, domain: str = None) -> float:
        """Get success rate for domain or overall"""
        if domain and domain in self.domain_stats:
            stats = self.domain_stats[domain]
            if stats['total'] == 0:
                return 0
            return stats['success'] / stats['total']
        
        if self.stats['total_requests'] == 0:
            return 0
        
        return self.stats['successful_requests'] / self.stats['total_requests']
    
    def should_alert(self, threshold: float = 0.8) -> bool:
        """Check if success rate is below threshold"""
        return self.get_success_rate() < threshold
    
    def get_report(self) -> dict:
        """Get detailed statistics report"""
        return {
            'overall': self.stats,
            'by_domain': self.domain_stats,
            'success_rate': self.get_success_rate(),
            'alerts': {
                'low_success_rate': self.should_alert(),
                'high_block_rate': self.stats['blocked_requests'] / max(1, self.stats['total_requests']) > 0.2,
                'captcha_issues': self.stats['captcha_encounters'] > 5
            }
        }