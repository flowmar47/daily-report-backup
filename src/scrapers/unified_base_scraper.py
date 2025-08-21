#!/usr/bin/env python3
"""
Unified Base Scraper
Consolidates all common scraping functionality into a single, well-architected base class
Eliminates code duplication and provides consistent patterns across all scrapers
"""

import asyncio
import os
import sys
import logging
import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, TimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'utils'))
sys.path.append(str(Path(__file__).parent.parent / 'utils'))
from env_config import EnvironmentConfig
from secure_session_manager import SecureSessionManager
from enhanced_error_handler import (
    resilient_operation, ErrorCategory, ErrorSeverity, RetryStrategy,
    retry_on_network_error, retry_on_authentication_error, circuit_breaker_protection,
    get_error_handler
)

logger = logging.getLogger(__name__)

class ScrapingError(Exception):
    """Base exception for scraping operations"""
    pass

class AuthenticationError(ScrapingError):
    """Authentication failed"""
    pass

class DataExtractionError(ScrapingError):
    """Data extraction failed"""
    pass

class SessionError(ScrapingError):
    """Session management failed"""
    pass

class UnifiedBaseScraper(ABC):
    """
    Unified base scraper that consolidates all common functionality
    Provides standardized patterns for authentication, data extraction, and error handling
    """
    
    def __init__(self, component: str = 'daily_report', config_overrides: Optional[Dict] = None):
        """
        Initialize unified base scraper
        
        Args:
            component: Component name for environment configuration
            config_overrides: Optional configuration overrides
        """
        self.component = component
        self.config_overrides = config_overrides or {}
        
        # Load environment configuration
        self.env_config = EnvironmentConfig(component)
        if not self.env_config.validate_credentials():
            raise ValueError(f"Invalid credentials for {component}")
        
        self.credentials = self.env_config.get_required_vars()
        self.optional_config = self.env_config.get_optional_vars()
        
        # Core properties to be set by subclasses
        self.site_name = getattr(self, 'SITE_NAME', 'unknown')
        self.base_url = getattr(self, 'BASE_URL', '')
        self.target_url = getattr(self, 'TARGET_URL', '')
        
        # Initialize directories
        self._setup_directories()
        
        # Initialize session management
        self.session_manager = SecureSessionManager()
        self.session_name = f"{self.site_name}_session"
        
        # Browser configuration
        self.browser_config = self._get_browser_config()
        
        # State tracking
        self.browser = None
        self.context = None
        self.page = None
        self.session_data = {}
        
        logger.info(f"🚀 {self.__class__.__name__} initialized for {self.site_name}")
    
    def _setup_directories(self):
        """Setup output and working directories"""
        base_dir = Path(__file__).parent.parent.parent
        
        self.output_dir = base_dir / 'output' / self.site_name
        self.reports_dir = base_dir / 'reports' / self.site_name
        self.logs_dir = base_dir / 'logs'
        self.cache_dir = base_dir / 'cache' / self.site_name
        
        for directory in [self.output_dir, self.reports_dir, self.logs_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_browser_config(self) -> Dict[str, Any]:
        """Get browser configuration with anti-detection settings"""
        return {
            'headless': not self.config_overrides.get('debug', False),
            'executable_path': '/usr/bin/chromium-browser',  # Use system Chromium
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'extra_http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            },
            'args': ['--no-sandbox', '--disable-dev-shm-usage'],  # Required for headless
            'ignore_https_errors': True
        }
    
    @resilient_operation(
        "initialize_browser",
        "scraper",
        ErrorCategory.BROWSER_AUTOMATION,
        ErrorSeverity.HIGH,
        RetryStrategy.EXPONENTIAL_BACKOFF,
        max_retries=3
    )
    async def initialize_browser(self) -> bool:
        """Initialize browser with session restoration"""
        try:
            playwright = await async_playwright().start()
            # Extract browser launch options (only valid launch options)
            valid_launch_options = ['headless', 'executable_path', 'args', 'ignore_default_args', 
                                   'handle_sigint', 'handle_sigterm', 'handle_sighup', 'timeout',
                                   'env', 'devtools', 'proxy', 'downloads_path', 'slow_mo',
                                   'traces_dir', 'chromium_sandbox', 'firefox_user_prefs']
            launch_options = {k: v for k, v in self.browser_config.items() if k in valid_launch_options}
            self.browser = await playwright.chromium.launch(**launch_options)
            
            # Try to restore session
            session_state = self.session_manager.load_session_state(self.session_name)
            
            if session_state:
                self.context = await self.browser.new_context(
                    viewport=self.browser_config['viewport'],
                    user_agent=self.browser_config['user_agent'],
                    extra_http_headers=self.browser_config['extra_http_headers'],
                    storage_state=session_state
                )
                logger.info(f"✅ Restored session for {self.site_name}")
            else:
                self.context = await self.browser.new_context(
                    viewport=self.browser_config['viewport'],
                    user_agent=self.browser_config['user_agent'],
                    extra_http_headers=self.browser_config['extra_http_headers']
                )
                logger.info(f"🆕 Created new session for {self.site_name}")
            
            self.page = await self.context.new_page()
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            await self.cleanup()
            raise SessionError(f"Browser initialization failed: {e}")
    
    @retry_on_authentication_error(max_retries=3)
    async def authenticate(self) -> bool:
        """Authenticate with the target site"""
        if not self.page:
            raise SessionError("Browser not initialized")
        
        try:
            # Check if already authenticated
            if await self._is_authenticated():
                logger.info(f"✅ Already authenticated with {self.site_name}")
                return True
            
            # Perform authentication
            success = await self._perform_authentication()
            
            if success:
                # Save session state
                session_state = await self.context.storage_state()
                self.session_manager.save_session_state(session_state, self.session_name)
                logger.info(f"✅ Authentication successful for {self.site_name}")
                return True
            else:
                raise AuthenticationError(f"Authentication failed for {self.site_name}")
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise AuthenticationError(f"Authentication failed: {e}")
    
    @resilient_operation(
        "scrape_data",
        "scraper",
        ErrorCategory.DATA_EXTRACTION,
        ErrorSeverity.HIGH,
        RetryStrategy.EXPONENTIAL_BACKOFF,
        max_retries=2
    )
    async def scrape_data(self) -> Dict[str, Any]:
        """Main scraping orchestration method"""
        try:
            # Initialize browser and authenticate
            await self.initialize_browser()
            await self.authenticate()
            
            # Navigate to target page
            await self._navigate_to_target()
            
            # Extract data using subclass implementation
            raw_data = await self._extract_data()
            
            # Validate extracted data
            validated_data = await self._validate_data(raw_data)
            
            # Process and structure data
            processed_data = await self._process_data(validated_data)
            
            # Save results
            output_file = await self._save_results(processed_data)
            
            logger.info(f"✅ Scraping completed successfully for {self.site_name}")
            return {
                'success': True,
                'data': processed_data,
                'output_file': str(output_file),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            await self._handle_error(e)
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            await self.cleanup()
    
    @retry_on_network_error(max_retries=3)
    async def _navigate_to_target(self):
        """Navigate to target URL with wait conditions"""
        if not self.target_url:
            raise ValueError("Target URL not set")
        
        try:
            # Try different wait strategies for better reliability
            try:
                # First try with domcontentloaded which is more reliable
                await self.page.goto(self.target_url, wait_until='domcontentloaded', timeout=60000)
                logger.info(f"✅ Page loaded with domcontentloaded: {self.target_url}")
            except Exception as nav_error:
                logger.warning(f"⚠️ Initial navigation failed, trying alternative approach: {nav_error}")
                # Fallback to commit which just waits for navigation to start
                await self.page.goto(self.target_url, wait_until='commit', timeout=30000)
                # Then wait for content to load
                await asyncio.sleep(5)
                logger.info(f"✅ Navigation started with commit: {self.target_url}")
            
            # Wait for any site-specific load conditions
            await self._wait_for_page_ready()
            
            logger.info(f"✅ Successfully navigated to {self.target_url}")
            
        except Exception as e:
            raise DataExtractionError(f"Navigation failed: {e}")
    
    async def _save_results(self, data: Dict[str, Any]) -> Path:
        """Save scraped results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.site_name}_data_{timestamp}.json"
        output_file = self.output_dir / filename
        
        try:
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            # Also save as latest
            latest_file = self.output_dir / f"latest_{self.site_name}_data.json"
            with open(latest_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"✅ Results saved to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            raise
    
    async def _handle_error(self, error: Exception):
        """Handle and log errors appropriately"""
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat(),
            'site': self.site_name,
            'target_url': self.target_url
        }
        
        # Save error log
        error_file = self.logs_dir / f"error_{self.site_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(error_file, 'w') as f:
                json.dump(error_data, f, indent=2)
        except Exception as save_error:
            logger.error(f"Failed to save error log: {save_error}")
        
        # Take screenshot if page exists
        if self.page:
            try:
                screenshot_file = self.logs_dir / f"error_screenshot_{self.site_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await self.page.screenshot(path=str(screenshot_file), full_page=True)
                logger.info(f"Error screenshot saved: {screenshot_file}")
            except Exception as screenshot_error:
                logger.error(f"Failed to take error screenshot: {screenshot_error}")
    
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
                
            self.page = None
            self.context = None
            self.browser = None
            
            logger.info(f"✅ Browser cleanup completed for {self.site_name}")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    # Abstract methods to be implemented by subclasses
    
    @abstractmethod
    async def _is_authenticated(self) -> bool:
        """Check if already authenticated with the site"""
        pass
    
    @abstractmethod
    async def _perform_authentication(self) -> bool:
        """Perform site-specific authentication"""
        pass
    
    @abstractmethod
    async def _wait_for_page_ready(self):
        """Wait for page-specific load conditions"""
        pass
    
    @abstractmethod
    async def _extract_data(self) -> Dict[str, Any]:
        """Extract raw data from the page"""
        pass
    
    @abstractmethod
    async def _validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted data"""
        pass
    
    @abstractmethod
    async def _process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and structure the validated data"""
        pass
    
    # Utility methods for subclasses
    
    async def wait_and_click(self, selector: str, timeout: int = 5000):
        """Wait for element and click it"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.click(selector)
            await asyncio.sleep(0.5)  # Brief pause after click
        except Exception as e:
            raise DataExtractionError(f"Failed to click {selector}: {e}")
    
    async def wait_and_type(self, selector: str, text: str, timeout: int = 5000):
        """Wait for element and type text"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.fill(selector, text)
            await asyncio.sleep(0.3)  # Brief pause after typing
        except Exception as e:
            raise DataExtractionError(f"Failed to type in {selector}: {e}")
    
    async def wait_for_element(self, selector: str, timeout: int = 5000) -> bool:
        """Wait for element to appear"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False
    
    async def get_element_text(self, selector: str) -> Optional[str]:
        """Get text content of element"""
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.text_content()
            return None
        except Exception as e:
            logger.warning(f"Failed to get text from {selector}: {e}")
            return None
    
    async def get_all_element_texts(self, selector: str) -> List[str]:
        """Get text content of all matching elements"""
        try:
            elements = await self.page.query_selector_all(selector)
            texts = []
            for element in elements:
                text = await element.text_content()
                if text and text.strip():
                    texts.append(text.strip())
            return texts
        except Exception as e:
            logger.warning(f"Failed to get texts from {selector}: {e}")
            return []