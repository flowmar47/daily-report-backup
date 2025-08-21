#!/usr/bin/env python3
"""
Unified MyMama Scraper
Consolidates all MyMama scraping functionality using the unified base scraper
Replaces multiple duplicate scraper implementations with single, well-architected class
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional, List
from pathlib import Path

from .unified_base_scraper import UnifiedBaseScraper, AuthenticationError, DataExtractionError
from ..data_processors.financial_alerts import FinancialAlertsProcessor
from ..data_processors.data_models import StructuredFinancialReport

logger = logging.getLogger(__name__)

class UnifiedMyMamaScraper(UnifiedBaseScraper):
    """
    Unified MyMama scraper implementing the base scraper pattern
    Handles authentication, data extraction, and processing for MyMama.uk
    """
    
    # Class constants
    SITE_NAME = 'mymama'
    BASE_URL = 'https://www.mymama.uk'
    TARGET_URL = 'https://www.mymama.uk/copy-of-alerts-essentials-1'
    
    def __init__(self, config_overrides: Optional[Dict] = None):
        """Initialize MyMama scraper"""
        super().__init__('daily_report', config_overrides)
        
        # MyMama-specific configuration
        self.username = self.credentials['MYMAMA_USERNAME']
        self.password = self.credentials['MYMAMA_PASSWORD']
        self.guest_password = self.optional_config.get('MYMAMA_GUEST_PASSWORD')
        
        # Initialize data processor
        self.processor = FinancialAlertsProcessor()
        
        # MyMama-specific selectors
        self.selectors = {
            'login': {
                'username': 'input[type="text"], input[type="email"]',
                'password': 'input[type="password"]',
                'submit': 'button[type="submit"], input[type="submit"]',
                'modal': '.modal, [role="dialog"]',
                'close_modal': '.modal-close, [aria-label="close"], .close'
            },
            'content': {
                'tables': 'table',
                'alerts': 'div.alert, div.signal, [class*="alert"], [class*="signal"]',
                'content_area': 'main, #content, .content, [role="main"]',
                'forex_section': '[data-testid="forex"], .forex-section, table:first-of-type',
                'options_section': '[data-testid="options"], .options-section',
                'earnings_section': '[data-testid="earnings"], .earnings-section'
            },
            'authentication_check': 'body:not(:has(input[type="password"]))'
        }
        
        logger.info(f"🎯 MyMama scraper configured for user: {self.username}")
    
    async def _is_authenticated(self) -> bool:
        """Check if already authenticated with MyMama"""
        try:
            # Navigate to target page to check authentication
            await self.page.goto(self.target_url, wait_until='domcontentloaded', timeout=15000)
            
            # Wait briefly for any authentication redirects
            await asyncio.sleep(2)
            
            # Check if we're on a login page or if password inputs are present
            password_inputs = await self.page.query_selector_all('input[type="password"]')
            current_url = self.page.url
            
            # If no password inputs and we're on the target page, we're authenticated
            is_authenticated = (
                len(password_inputs) == 0 and 
                'login' not in current_url.lower() and
                'sign' not in current_url.lower()
            )
            
            if is_authenticated:
                logger.info("✅ Already authenticated with MyMama")
            else:
                logger.info("🔐 Authentication required for MyMama")
            
            return is_authenticated
            
        except Exception as e:
            logger.warning(f"Authentication check failed: {e}")
            return False
    
    async def _perform_authentication(self) -> bool:
        """Perform MyMama authentication"""
        try:
            logger.info("🔐 Starting MyMama authentication...")
            
            # Navigate to login page if needed
            current_url = self.page.url
            if 'login' not in current_url.lower():
                await self.page.goto(f"{self.BASE_URL}/login", wait_until='domcontentloaded')
            
            # Handle any modal dialogs that might appear
            await self._handle_modals()
            
            # Find and fill username field
            await self.wait_and_type(self.selectors['login']['username'], self.username)
            logger.info("✅ Username entered")
            
            # Find and fill password field
            await self.wait_and_type(self.selectors['login']['password'], self.password)
            logger.info("✅ Password entered")
            
            # Submit login form
            await self.wait_and_click(self.selectors['login']['submit'])
            logger.info("✅ Login form submitted")
            
            # Wait for authentication to complete
            await asyncio.sleep(3)
            
            # Handle guest password if prompted
            if self.guest_password:
                guest_password_input = await self.page.query_selector('input[type="password"]')
                if guest_password_input:
                    await self.wait_and_type('input[type="password"]', self.guest_password)
                    await self.wait_and_click(self.selectors['login']['submit'])
                    await asyncio.sleep(2)
                    logger.info("✅ Guest password entered")
            
            # Verify authentication success
            await asyncio.sleep(2)
            password_inputs = await self.page.query_selector_all('input[type="password"]')
            
            if len(password_inputs) == 0:
                logger.info("✅ MyMama authentication successful")
                return True
            else:
                logger.error("❌ MyMama authentication failed - still on login page")
                return False
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(f"MyMama authentication failed: {e}")
    
    async def _handle_modals(self):
        """Handle any modal dialogs that might appear"""
        try:
            modal = await self.page.query_selector(self.selectors['login']['modal'])
            if modal:
                close_btn = await self.page.query_selector(self.selectors['login']['close_modal'])
                if close_btn:
                    await close_btn.click()
                    await asyncio.sleep(1)
                    logger.info("✅ Closed modal dialog")
        except Exception as e:
            logger.debug(f"No modal to handle: {e}")
    
    async def _wait_for_page_ready(self):
        """Wait for MyMama page-specific load conditions"""
        try:
            # Wait for main content area
            await self.wait_for_element(self.selectors['content']['content_area'], timeout=10000)
            
            # Wait for tables or alerts to load
            tables_loaded = await self.wait_for_element(self.selectors['content']['tables'], timeout=5000)
            alerts_loaded = await self.wait_for_element(self.selectors['content']['alerts'], timeout=5000)
            
            if not (tables_loaded or alerts_loaded):
                logger.warning("No tables or alerts found - page may not have loaded completely")
            
            # Additional wait for dynamic content
            await asyncio.sleep(2)
            
            logger.info("✅ MyMama page ready for data extraction")
            
        except Exception as e:
            logger.warning(f"Page ready check had issues: {e}")
    
    async def _extract_data(self) -> Dict[str, Any]:
        """Extract raw data from MyMama page"""
        try:
            logger.info("🔍 Starting data extraction from MyMama...")
            
            # Get page content
            page_content = await self.page.content()
            page_text = await self.page.inner_text('body')
            
            # Extract tables
            tables_data = await self._extract_tables()
            
            # Extract forex data
            forex_data = await self._extract_forex_section()
            
            # Extract options data
            options_data = await self._extract_options_section()
            
            # Extract earnings data
            earnings_data = await self._extract_earnings_section()
            
            raw_data = {
                'page_content': page_content,
                'page_text': page_text,
                'tables': tables_data,
                'forex': forex_data,
                'options': options_data,
                'earnings': earnings_data,
                'extraction_timestamp': self._get_timestamp(),
                'source_url': self.page.url
            }
            
            logger.info(f"✅ Extracted {len(tables_data)} tables and structured sections")
            return raw_data
            
        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
            raise DataExtractionError(f"Failed to extract data from MyMama: {e}")
    
    async def _extract_tables(self) -> List[Dict[str, Any]]:
        """Extract all tables from the page"""
        tables = []
        try:
            table_elements = await self.page.query_selector_all('table')
            
            for i, table in enumerate(table_elements):
                table_html = await table.inner_html()
                table_text = await table.inner_text()
                
                tables.append({
                    'index': i,
                    'html': table_html,
                    'text': table_text,
                    'row_count': len(table_text.split('\n')) if table_text else 0
                })
            
            logger.info(f"✅ Extracted {len(tables)} tables")
            return tables
            
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return []
    
    async def _extract_forex_section(self) -> Dict[str, Any]:
        """Extract forex-specific data"""
        try:
            # Try multiple selectors for forex section
            forex_selectors = [
                self.selectors['content']['forex_section'],
                'table:first-of-type',
                '.forex, .currency',
                '[data-section="forex"]'
            ]
            
            for selector in forex_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    return {
                        'html': await element.inner_html(),
                        'text': await element.inner_text(),
                        'selector_used': selector
                    }
            
            # If no specific forex section, get first table
            first_table = await self.page.query_selector('table')
            if first_table:
                return {
                    'html': await first_table.inner_html(),
                    'text': await first_table.inner_text(),
                    'selector_used': 'table:first-of-type'
                }
            
            return {'html': '', 'text': '', 'selector_used': 'none'}
            
        except Exception as e:
            logger.error(f"Forex extraction failed: {e}")
            return {'html': '', 'text': '', 'error': str(e)}
    
    async def _extract_options_section(self) -> Dict[str, Any]:
        """Extract options-specific data"""
        try:
            # Look for options-related content
            options_selectors = [
                self.selectors['content']['options_section'],
                '[data-section="options"]',
                '.options, .equity',
                'table:nth-of-type(2)'
            ]
            
            for selector in options_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    return {
                        'html': await element.inner_html(),
                        'text': await element.inner_text(),
                        'selector_used': selector
                    }
            
            return {'html': '', 'text': '', 'selector_used': 'none'}
            
        except Exception as e:
            logger.error(f"Options extraction failed: {e}")
            return {'html': '', 'text': '', 'error': str(e)}
    
    async def _extract_earnings_section(self) -> Dict[str, Any]:
        """Extract earnings-specific data"""
        try:
            # Look for earnings-related content
            earnings_selectors = [
                self.selectors['content']['earnings_section'],
                '[data-section="earnings"]',
                '.earnings, .premium',
                'table:last-of-type'
            ]
            
            for selector in earnings_selectors:
                element = await self.page.query_selector(selector)
                if element:
                    return {
                        'html': await element.inner_html(),
                        'text': await element.inner_text(),
                        'selector_used': selector
                    }
            
            return {'html': '', 'text': '', 'selector_used': 'none'}
            
        except Exception as e:
            logger.error(f"Earnings extraction failed: {e}")
            return {'html': '', 'text': '', 'error': str(e)}
    
    async def _validate_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted MyMama data"""
        try:
            validation_results = {
                'is_valid': True,
                'issues': [],
                'data_quality_score': 0,
                'section_status': {}
            }
            
            # Check if we have any content
            if not data.get('page_text'):
                validation_results['is_valid'] = False
                validation_results['issues'].append('No page text extracted')
            
            # Validate forex section
            forex_data = data.get('forex', {})
            if forex_data.get('text'):
                validation_results['section_status']['forex'] = 'present'
                validation_results['data_quality_score'] += 1
            else:
                validation_results['section_status']['forex'] = 'missing'
                validation_results['issues'].append('No forex data found')
            
            # Validate options section
            options_data = data.get('options', {})
            if options_data.get('text'):
                validation_results['section_status']['options'] = 'present'
                validation_results['data_quality_score'] += 1
            else:
                validation_results['section_status']['options'] = 'missing'
                validation_results['issues'].append('No options data found')
            
            # Validate earnings section
            earnings_data = data.get('earnings', {})
            if earnings_data.get('text'):
                validation_results['section_status']['earnings'] = 'present'
                validation_results['data_quality_score'] += 1
            else:
                validation_results['section_status']['earnings'] = 'missing'
                validation_results['issues'].append('No earnings data found')
            
            # Check for authentication issues
            page_text = data.get('page_text', '').lower()
            if 'login' in page_text or 'sign in' in page_text:
                validation_results['is_valid'] = False
                validation_results['issues'].append('Authentication may have failed')
            
            # Calculate final quality score
            max_score = 3  # forex, options, earnings
            validation_results['data_quality_score'] = validation_results['data_quality_score'] / max_score
            
            if validation_results['data_quality_score'] < 0.5:
                validation_results['is_valid'] = False
                validation_results['issues'].append('Low data quality score')
            
            data['validation'] = validation_results
            
            if validation_results['is_valid']:
                logger.info(f"✅ Data validation passed (score: {validation_results['data_quality_score']:.2f})")
            else:
                logger.warning(f"⚠️ Data validation issues: {validation_results['issues']}")
            
            return data
            
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            data['validation'] = {'is_valid': False, 'error': str(e)}
            return data
    
    async def _process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and structure the validated data"""
        try:
            logger.info("🔄 Processing MyMama data...")
            
            # Use the financial alerts processor
            structured_report = await asyncio.to_thread(
                self.processor.process_scraped_data,
                data.get('page_content', ''),
                data.get('page_text', '')
            )
            
            # Convert structured report to dict format for consistency
            processed_data = {
                'forex_forecasts': [f.to_dict() for f in structured_report.forex_forecasts],
                'options_trades': [o.to_dict() for o in structured_report.options_trades],
                'stock_crypto_forecasts': [s.to_dict() for s in structured_report.stock_crypto_forecasts],
                'swing_trades': [sw.to_dict() for sw in structured_report.swing_trades],
                'day_trades': [d.to_dict() for d in structured_report.day_trades],
                'earnings_reports': [e.to_dict() for e in structured_report.earnings_reports],
                'table_sections': [t.to_dict() for t in structured_report.table_sections],
                'summary_stats': structured_report.get_summary_stats(),
                'source': 'mymama',
                'source_url': data.get('source_url'),
                'extraction_timestamp': data.get('extraction_timestamp'),
                'validation_results': data.get('validation'),
                'processing_timestamp': self._get_timestamp()
            }
            
            logger.info("✅ Data processing completed")
            return processed_data
            
        except Exception as e:
            logger.error(f"Data processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'raw_data': data
            }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()

# Convenience function for backwards compatibility
async def scrape_mymama_data(config_overrides: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Convenience function to scrape MyMama data
    
    Args:
        config_overrides: Optional configuration overrides
        
    Returns:
        Dictionary containing scraped and processed data
    """
    scraper = UnifiedMyMamaScraper(config_overrides)
    return await scraper.scrape_data()

if __name__ == "__main__":
    async def main():
        """Test the scraper"""
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        try:
            result = await scrape_mymama_data({'debug': True})
            
            if result['success']:
                print("✅ Scraping successful!")
                print(f"Data saved to: {result['output_file']}")
            else:
                print(f"❌ Scraping failed: {result['error']}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    asyncio.run(main())