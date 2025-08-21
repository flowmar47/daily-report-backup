#!/usr/bin/env python3
"""
Multi-API Price Validation System
Fetches prices from multiple sources and validates consensus
ZERO TOLERANCE for fake or unvalidated prices
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import statistics
import os
import sys
from dataclasses import dataclass
from pathlib import Path

# Add Signals directory to path for yfinance helper
current_dir = Path(__file__).parent
signals_dir = current_dir.parent / 'Signals' / 'src'
if str(signals_dir) not in sys.path:
    sys.path.append(str(signals_dir))

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class PriceData:
    """Price data with source and timestamp"""
    pair: str
    price: float
    source: str
    timestamp: datetime
    
@dataclass
class ValidationResult:
    """Result of price validation"""
    pair: str
    consensus_price: Optional[float]
    sources_count: int
    variance: float
    is_valid: bool
    reason: str

class MultiAPIValidator:
    """Enhanced multi-source forex price validator with yfinance integration"""
    
    def __init__(self):
        # Import yfinance helper
        try:
            from yfinance_helper import yfinance_helper
            self.yfinance_helper = yfinance_helper
            logger.info("yfinance helper loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load yfinance helper: {e}")
            self.yfinance_helper = None
        
        # Import enhanced data fetcher for Alpha Vantage and Twelve Data
        try:
            from data_fetcher import data_fetcher
            self.data_fetcher = data_fetcher
            logger.info("Enhanced data fetcher loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load enhanced data fetcher: {e}")
            self.data_fetcher = None
            
        # API configurations
        self.apis = {
            'exchangerate': {
                'key': 'c554d55ee2da8edcf00d3fd0',
                'base_url': 'https://v6.exchangerate-api.com/v6',
                'limit_per_day': 1500
            },
            'fixer': {
                'key': '583204002b746479a429c85acabc2809',
                'base_url': 'http://data.fixer.io/api',
                'limit_per_day': 100
            },
            'currencyapi': {
                'key': 'cur_live_rfaFYDdtG2L7FmviqMWhSL708hOAhh5sV3y4KGTV',
                'base_url': 'https://api.currencyapi.com/v3',
                'limit_per_day': 300
            },
            'freecurrency': {
                'key': 'fca_live_gjTzt4HGAfzZumDbZFgUXG6etSKYT54s2yf5N5Hf',
                'base_url': 'https://api.freecurrencyapi.com/v1',
                'limit_per_day': 5000
            },
            'exchangerates': {
                'key': 'e33eb2e6a8ede751b51c5c7f60900d78',
                'base_url': 'http://api.exchangeratesapi.io/v1',
                'limit_per_day': 250
            }
        }
        
        # Price validation ranges (reject if outside these bounds)
        self.valid_ranges = {
            'EURUSD': (0.95, 1.25),
            'GBPUSD': (1.15, 1.45),
            'USDJPY': (130, 160),
            'CHFJPY': (165, 190),
            'USDCAD': (1.25, 1.45),
            'USDCHF': (0.80, 1.05),
            'EURGBP': (0.80, 0.95),
            'EURJPY': (140, 170),
            'GBPJPY': (170, 200),
            'AUDCAD': (0.85, 1.05),
            'AUDUSD': (0.60, 0.80),
            'NZDUSD': (0.55, 0.75)
        }
        
        # Maximum allowed variance between sources (0.8% - more lenient for more sources)
        self.max_variance = 0.008
        
        # Minimum required sources for validation (3 sources for better accuracy)
        self.min_sources = 3
        
        # Price cache (5 minute TTL for rate limiting optimization)
        self.price_cache = {}
        self.cache_ttl = 300
        
    async def get_validated_price(self, pair: str) -> ValidationResult:
        """Get validated price for currency pair from multiple sources"""
        
        # Use file-based cache for persistence across runs
        try:
            from api_cache import api_cache
            cache_key = f"validated_price_{pair}"
            cached = api_cache.get(cache_key, 'forex_price')
            
            if cached:
                logger.info(f"Using cached validated price for {pair}: {cached['price']}")
                return ValidationResult(
                    pair=pair,
                    consensus_price=cached['price'],
                    sources_count=cached['sources'],
                    variance=cached['variance'],
                    is_valid=True,
                    reason="Cached validated price"
                )
        except:
            pass  # Fall back to in-memory cache
        
        # Check in-memory cache as fallback
        cache_key = pair
        if cache_key in self.price_cache:
            cached_data = self.price_cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < timedelta(seconds=self.cache_ttl):
                logger.info(f"Using cached price for {pair}: {cached_data['price']}")
                return ValidationResult(
                    pair=pair,
                    consensus_price=cached_data['price'],
                    sources_count=cached_data['sources'],
                    variance=cached_data['variance'],
                    is_valid=True,
                    reason="Cached validated price"
                )
        
        # Fetch from multiple APIs concurrently
        prices = await self._fetch_prices_from_all_apis(pair)
        
        if len(prices) < self.min_sources:
            logger.error(f"Insufficient sources for {pair}: {len(prices)} < {self.min_sources}")
            return ValidationResult(
                pair=pair,
                consensus_price=None,
                sources_count=len(prices),
                variance=0.0,
                is_valid=False,
                reason=f"Only {len(prices)} sources available, need minimum {self.min_sources}"
            )
        
        # Validate price range
        price_values = [p.price for p in prices]
        
        for price in price_values:
            if not self._is_price_in_valid_range(pair, price):
                logger.error(f"Price {price} for {pair} outside valid range {self.valid_ranges.get(pair)}")
                return ValidationResult(
                    pair=pair,
                    consensus_price=None,
                    sources_count=len(prices),
                    variance=0.0,
                    is_valid=False,
                    reason=f"Price {price} outside valid range"
                )
        
        # Calculate variance between sources
        mean_price = statistics.mean(price_values)
        variance = max(abs(p - mean_price) / mean_price for p in price_values)
        
        if variance > self.max_variance:
            logger.error(f"High variance for {pair}: {variance:.4f} > {self.max_variance}")
            return ValidationResult(
                pair=pair,
                consensus_price=None,
                sources_count=len(prices),
                variance=variance,
                is_valid=False,
                reason=f"Variance {variance:.4f} exceeds maximum {self.max_variance}"
            )
        
        # Price is validated - cache it
        consensus_price = round(mean_price, 5)
        cache_data = {
            'price': consensus_price,
            'timestamp': datetime.now(),
            'sources': len(prices),
            'variance': variance
        }
        self.price_cache[cache_key] = cache_data
        
        # Also save to file cache
        try:
            from api_cache import api_cache
            api_cache.set(f"validated_price_{pair}", cache_data, 'forex_price')
        except:
            pass
        
        logger.info(f"Validated price for {pair}: {consensus_price} from {len(prices)} sources, variance: {variance:.4f}")
        
        return ValidationResult(
            pair=pair,
            consensus_price=consensus_price,
            sources_count=len(prices),
            variance=variance,
            is_valid=True,
            reason="Successfully validated"
        )
    
    async def _fetch_prices_from_all_apis(self, pair: str) -> List[PriceData]:
        """Enhanced price fetching from all available APIs including yfinance"""
        tasks = []
        
        # Priority 1: yfinance (free, unlimited, reliable)
        if self.yfinance_helper:
            tasks.append(self._fetch_yfinance_price(pair))
        
        # Priority 2: Enhanced data fetcher (Alpha Vantage, Twelve Data)
        if self.data_fetcher:
            tasks.append(self._fetch_enhanced_price(pair))
        
        # Priority 3: Traditional forex APIs  
        tasks.append(self._fetch_exchangerate_api(pair))
        tasks.append(self._fetch_freecurrency_api(pair))
        tasks.append(self._fetch_currencyapi(pair))
        
        # Priority 4: Lower limit APIs (use sparingly)
        tasks.append(self._fetch_fixer_api(pair))
        tasks.append(self._fetch_exchangerates_api(pair))
        
        # Execute all API calls concurrently with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), 
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching prices for {pair}")
            return []
        
        # Filter out failed calls and None results
        valid_prices = []
        for i, result in enumerate(results):
            if isinstance(result, PriceData):
                valid_prices.append(result)
                logger.debug(f"Successfully fetched price from source {result.source} for {pair}: {result.price}")
            elif isinstance(result, Exception):
                logger.warning(f"API call {i} failed for {pair}: {result}")
            elif result is None:
                logger.debug(f"API call {i} returned None for {pair}")
        
        logger.info(f"Fetched {len(valid_prices)} valid prices for {pair} from {len(tasks)} sources")
        return valid_prices
    
    async def _fetch_yfinance_price(self, pair: str) -> Optional[PriceData]:
        """Fetch current price from yfinance (highest priority)"""
        try:
            if not self.yfinance_helper:
                return None
            
            # Run yfinance in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            price = await loop.run_in_executor(
                None, 
                self.yfinance_helper.get_current_price, 
                pair
            )
            
            if price and price > 0:
                return PriceData(
                    pair=pair,
                    price=float(price),
                    source='yfinance',
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.debug(f"yfinance price fetch error for {pair}: {e}")
        
        return None
    
    async def _fetch_enhanced_price(self, pair: str) -> Optional[PriceData]:
        """Fetch price from enhanced data fetcher (Alpha Vantage/Twelve Data)"""
        try:
            if not self.data_fetcher:
                return None
            
            # Run data fetcher in thread pool
            loop = asyncio.get_event_loop()
            price = await loop.run_in_executor(
                None,
                self.data_fetcher.get_current_price_validated,
                pair
            )
            
            if price and price > 0:
                return PriceData(
                    pair=pair,
                    price=float(price),
                    source='enhanced_data_fetcher',
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.debug(f"Enhanced data fetcher price error for {pair}: {e}")
        
        return None
    
    async def _fetch_exchangerate_api(self, pair: str) -> Optional[PriceData]:
        """Fetch from ExchangeRate-API"""
        try:
            base_currency = pair[:3]
            target_currency = pair[3:]
            
            url = f"{self.apis['exchangerate']['base_url']}/{self.apis['exchangerate']['key']}/pair/{base_currency}/{target_currency}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('result') == 'success':
                            price = float(data['conversion_rate'])
                            return PriceData(
                                pair=pair,
                                price=price,
                                source='exchangerate',
                                timestamp=datetime.now()
                            )
            return None
        except Exception as e:
            logger.warning(f"ExchangeRate-API error for {pair}: {e}")
            return None
    
    async def _fetch_fixer_api(self, pair: str) -> Optional[PriceData]:
        """Fetch from Fixer.io"""
        try:
            base_currency = pair[:3]
            target_currency = pair[3:]
            
            url = f"{self.apis['fixer']['base_url']}/latest?access_key={self.apis['fixer']['key']}&base={base_currency}&symbols={target_currency}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            price = float(data['rates'][target_currency])
                            return PriceData(
                                pair=pair,
                                price=price,
                                source='fixer',
                                timestamp=datetime.now()
                            )
            return None
        except Exception as e:
            logger.warning(f"Fixer.io error for {pair}: {e}")
            return None
    
    async def _fetch_currencyapi(self, pair: str) -> Optional[PriceData]:
        """Fetch from CurrencyAPI"""
        try:
            base_currency = pair[:3]
            target_currency = pair[3:]
            
            url = f"{self.apis['currencyapi']['base_url']}/latest?apikey={self.apis['currencyapi']['key']}&base_currency={base_currency}&currencies={target_currency}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if target_currency in data.get('data', {}):
                            price = float(data['data'][target_currency]['value'])
                            return PriceData(
                                pair=pair,
                                price=price,
                                source='currencyapi',
                                timestamp=datetime.now()
                            )
            return None
        except Exception as e:
            logger.warning(f"CurrencyAPI error for {pair}: {e}")
            return None
    
    async def _fetch_freecurrency_api(self, pair: str) -> Optional[PriceData]:
        """Fetch from FreeCurrencyAPI"""
        try:
            base_currency = pair[:3]
            target_currency = pair[3:]
            
            url = f"{self.apis['freecurrency']['base_url']}/latest?apikey={self.apis['freecurrency']['key']}&base_currency={base_currency}&currencies={target_currency}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if target_currency in data.get('data', {}):
                            price = float(data['data'][target_currency])
                            return PriceData(
                                pair=pair,
                                price=price,
                                source='freecurrency',
                                timestamp=datetime.now()
                            )
            return None
        except Exception as e:
            logger.warning(f"FreeCurrencyAPI error for {pair}: {e}")
            return None
    
    async def _fetch_exchangerates_api(self, pair: str) -> Optional[PriceData]:
        """Fetch from ExchangeRatesAPI"""
        try:
            base_currency = pair[:3]
            target_currency = pair[3:]
            
            url = f"{self.apis['exchangerates']['base_url']}/latest?access_key={self.apis['exchangerates']['key']}&base={base_currency}&symbols={target_currency}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            price = float(data['rates'][target_currency])
                            return PriceData(
                                pair=pair,
                                price=price,
                                source='exchangerates',
                                timestamp=datetime.now()
                            )
            return None
        except Exception as e:
            logger.warning(f"ExchangeRatesAPI error for {pair}: {e}")
            return None
    
    def _is_price_in_valid_range(self, pair: str, price: float) -> bool:
        """Check if price is within valid range for the currency pair"""
        if pair not in self.valid_ranges:
            logger.warning(f"No validation range defined for {pair}")
            return True  # Allow if no range defined
        
        min_price, max_price = self.valid_ranges[pair]
        return min_price <= price <= max_price
    
    async def validate_multiple_pairs(self, pairs: List[str]) -> Dict[str, ValidationResult]:
        """Validate prices for multiple currency pairs"""
        results = {}
        
        # Process pairs concurrently
        tasks = [self.get_validated_price(pair) for pair in pairs]
        validation_results = await asyncio.gather(*tasks)
        
        for pair, result in zip(pairs, validation_results):
            results[pair] = result
        
        return results
    
    async def get_validation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive validation statistics"""
        try:
            stats = {
                'cache_entries': len(self.price_cache),
                'max_variance_threshold': self.max_variance,
                'min_sources_required': self.min_sources,
                'cache_ttl_seconds': self.cache_ttl,
                'available_integrations': {
                    'yfinance': self.yfinance_helper is not None,
                    'enhanced_data_fetcher': self.data_fetcher is not None
                },
                'supported_pairs': list(self.valid_ranges.keys()),
                'api_sources': list(self.apis.keys())
            }
            
            # Test a quick validation to check system health
            try:
                test_result = await self.get_validated_price('EURUSD')
                stats['system_health'] = {
                    'status': 'healthy' if test_result.is_valid else 'degraded',
                    'test_sources': test_result.sources_count,
                    'test_variance': test_result.variance
                }
            except Exception as e:
                stats['system_health'] = {'status': 'error', 'error': str(e)}
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting validation statistics: {e}")
            return {'error': str(e)}
    
    def clear_cache(self):
        """Clear price cache"""
        self.price_cache.clear()
        logger.info("Price validation cache cleared")
    
    def update_valid_ranges(self, new_ranges: Dict[str, Tuple[float, float]]):
        """Update valid price ranges for currency pairs"""
        self.valid_ranges.update(new_ranges)
        logger.info(f"Updated valid ranges for {len(new_ranges)} pairs")
    
    async def batch_validate_with_details(self, pairs: List[str]) -> Dict[str, Dict]:
        """Get detailed validation results for multiple pairs"""
        results = await self.validate_multiple_pairs(pairs)
        
        detailed_results = {}
        for pair, result in results.items():
            detailed_results[pair] = {
                'price': result.consensus_price,
                'is_valid': result.is_valid,
                'sources_count': result.sources_count,
                'variance': result.variance,
                'reason': result.reason,
                'timestamp': datetime.now().isoformat()
            }
        
        return detailed_results

# Global validator instance
price_validator = MultiAPIValidator()

async def get_validated_prices(pairs: List[str]) -> Dict[str, float]:
    """
    Get validated prices for multiple pairs
    Returns only successfully validated prices
    """
    results = await price_validator.validate_multiple_pairs(pairs)
    
    validated_prices = {}
    for pair, result in results.items():
        if result.is_valid and result.consensus_price is not None:
            validated_prices[pair] = result.consensus_price
        else:
            logger.error(f"Failed to validate {pair}: {result.reason}")
    
    return validated_prices

async def get_single_validated_price(pair: str) -> Optional[float]:
    """Get validated price for a single currency pair"""
    result = await price_validator.get_validated_price(pair)
    
    if result.is_valid and result.consensus_price is not None:
        return result.consensus_price
    else:
        logger.error(f"Failed to validate {pair}: {result.reason}")
        return None

if __name__ == "__main__":
    # Test the validator
    async def test_validator():
        pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'CHFJPY', 'USDCAD']
        results = await price_validator.validate_multiple_pairs(pairs)
        
        for pair, result in results.items():
            if result.is_valid:
                print(f"✅ {pair}: {result.consensus_price} (sources: {result.sources_count}, variance: {result.variance:.4f})")
            else:
                print(f"❌ {pair}: {result.reason}")
    
    asyncio.run(test_validator())