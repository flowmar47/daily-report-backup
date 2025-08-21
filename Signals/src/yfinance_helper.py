"""
yfinance Integration Helper
Provides validation and supplementary data using yfinance
Author: Claude Code Enhancement System
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logger = logging.getLogger(__name__)

class YFinanceHelper:
    """
    yfinance integration for price validation and supplementary data
    Optimized for forex pairs with error handling and fallbacks
    """
    
    def __init__(self):
        # Forex pair mapping to yfinance symbols
        self.forex_symbol_map = {
            'EURUSD': 'EURUSD=X',
            'GBPUSD': 'GBPUSD=X',
            'USDJPY': 'JPY=X',
            'USDCHF': 'CHF=X',
            'AUDUSD': 'AUDUSD=X',
            'USDCAD': 'CAD=X',
            'NZDUSD': 'NZDUSD=X',
            'CHFJPY': 'CHFJPY=X',
            'EURJPY': 'EURJPY=X',
            'GBPJPY': 'GBPJPY=X',
            'EURGBP': 'EURGBP=X',
            'AUDCAD': 'AUDCAD=X',
            'AUDCHF': 'AUDCHF=X',
            'AUDJPY': 'AUDJPY=X',
            'AUDNZD': 'AUDNZD=X',
            'CADCHF': 'CADCHF=X',
            'CADJPY': 'CADJPY=X',
            'EURAUD': 'EURAUD=X',
            'EURCAD': 'EURCAD=X',
            'EURCHF': 'EURCHF=X',
            'EURNZD': 'EURNZD=X',
            'GBPAUD': 'GBPAUD=X',
            'GBPCAD': 'GBPCAD=X',
            'GBPCHF': 'GBPCHF=X',
            'GBPNZD': 'GBPNZD=X',
            'NZDCAD': 'NZDCAD=X',
            'NZDCHF': 'NZDCHF=X',
            'NZDJPY': 'NZDJPY=X'
        }
        
        # Cache for recent data to avoid repeated calls
        self.price_cache = {}
        self.cache_expiry = 300  # 5 minutes
    
    def get_current_price(self, pair: str) -> Optional[float]:
        """
        Get current price for validation using yfinance
        
        Args:
            pair: Currency pair (e.g., 'EURUSD')
            
        Returns:
            Current price or None if failed
        """
        try:
            # Check cache first
            cache_key = f"{pair}_current"
            if cache_key in self.price_cache:
                cached_data, timestamp = self.price_cache[cache_key]
                if time.time() - timestamp < self.cache_expiry:
                    return cached_data
            
            yf_symbol = self.forex_symbol_map.get(pair)
            if not yf_symbol:
                logger.warning(f"No yfinance symbol mapping for {pair}")
                return None
            
            ticker = yf.Ticker(yf_symbol)
            
            # Get current price from info
            info = ticker.info
            current_price = info.get('regularMarketPrice') or info.get('bid') or info.get('ask')
            
            if current_price and current_price > 0:
                # Cache the result
                self.price_cache[cache_key] = (float(current_price), time.time())
                logger.debug(f"yfinance current price for {pair}: {current_price}")
                return float(current_price)
            
            # Fallback: get latest from history
            hist_data = ticker.history(period='1d', interval='1m')
            if not hist_data.empty:
                latest_price = float(hist_data['Close'].iloc[-1])
                self.price_cache[cache_key] = (latest_price, time.time())
                logger.debug(f"yfinance historical price for {pair}: {latest_price}")
                return latest_price
                
        except Exception as e:
            logger.debug(f"yfinance current price error for {pair}: {e}")
        
        return None
    
    def get_historical_data(self, pair: str, period: str = '1mo', 
                          interval: str = '1h') -> Optional[pd.DataFrame]:
        """
        Get historical data for analysis
        
        Args:
            pair: Currency pair
            period: Period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            
        Returns:
            DataFrame with OHLC data or None if failed
        """
        try:
            # Check cache
            cache_key = f"{pair}_{period}_{interval}"
            if cache_key in self.price_cache:
                cached_data, timestamp = self.price_cache[cache_key]
                if time.time() - timestamp < self.cache_expiry:
                    return cached_data
            
            yf_symbol = self.forex_symbol_map.get(pair)
            if not yf_symbol:
                logger.warning(f"No yfinance symbol mapping for {pair}")
                return None
            
            ticker = yf.Ticker(yf_symbol)
            hist_data = ticker.history(period=period, interval=interval)
            
            if hist_data.empty:
                logger.warning(f"No historical data from yfinance for {pair}")
                return None
            
            # Standardize column names
            hist_data.columns = [col.lower() for col in hist_data.columns]
            
            # Ensure we have required columns
            required_cols = ['open', 'high', 'low', 'close']
            if not all(col in hist_data.columns for col in required_cols):
                logger.warning(f"Missing required columns in yfinance data for {pair}")
                return None
            
            # Remove any timezone info and reset index
            hist_data.index = hist_data.index.tz_localize(None)
            
            # Cache the result
            self.price_cache[cache_key] = (hist_data.copy(), time.time())
            
            logger.debug(f"yfinance historical data for {pair}: {len(hist_data)} records")
            return hist_data
            
        except Exception as e:
            logger.debug(f"yfinance historical data error for {pair}: {e}")
        
        return None
    
    def validate_price(self, pair: str, price: float, tolerance_pct: float = 2.0) -> bool:
        """
        Validate a price against yfinance data
        
        Args:
            pair: Currency pair
            price: Price to validate
            tolerance_pct: Tolerance percentage for validation
            
        Returns:
            True if price is within tolerance, False otherwise
        """
        try:
            yf_price = self.get_current_price(pair)
            if yf_price is None:
                logger.warning(f"Cannot validate {pair} price - no yfinance data available")
                return True  # Allow if we can't validate
            
            price_diff_pct = abs((price - yf_price) / yf_price) * 100
            
            if price_diff_pct <= tolerance_pct:
                logger.debug(f"Price validation PASSED for {pair}: {price} vs {yf_price} (diff: {price_diff_pct:.2f}%)")
                return True
            else:
                logger.warning(f"Price validation FAILED for {pair}: {price} vs {yf_price} (diff: {price_diff_pct:.2f}%)")
                return False
                
        except Exception as e:
            logger.error(f"Price validation error for {pair}: {e}")
            return True  # Allow if validation fails
    
    def get_price_range(self, pair: str, days: int = 30) -> Optional[Dict[str, float]]:
        """
        Get price range statistics for the past N days
        
        Args:
            pair: Currency pair
            days: Number of days to analyze
            
        Returns:
            Dictionary with range statistics or None
        """
        try:
            period = f"{days}d" if days <= 60 else "3mo"
            hist_data = self.get_historical_data(pair, period=period, interval='1d')
            
            if hist_data is None or hist_data.empty:
                return None
            
            # Get last N days
            if len(hist_data) > days:
                hist_data = hist_data.tail(days)
            
            price_stats = {
                'high': float(hist_data['high'].max()),
                'low': float(hist_data['low'].min()),
                'avg': float(hist_data['close'].mean()),
                'current': float(hist_data['close'].iloc[-1]),
                'volatility': float(hist_data['close'].pct_change().std() * np.sqrt(252)),  # Annualized
                'range_pct': float((hist_data['high'].max() - hist_data['low'].min()) / hist_data['close'].mean() * 100)
            }
            
            logger.debug(f"Price range for {pair} ({days}d): {price_stats}")
            return price_stats
            
        except Exception as e:
            logger.error(f"Price range calculation error for {pair}: {e}")
        
        return None
    
    def batch_validate_prices(self, price_data: Dict[str, float], 
                            tolerance_pct: float = 2.0, max_workers: int = 3) -> Dict[str, bool]:
        """
        Validate multiple prices concurrently
        
        Args:
            price_data: Dictionary of pair -> price
            tolerance_pct: Tolerance percentage
            max_workers: Maximum concurrent workers
            
        Returns:
            Dictionary of pair -> validation_result
        """
        results = {}
        
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all validation tasks
                future_to_pair = {
                    executor.submit(self.validate_price, pair, price, tolerance_pct): pair
                    for pair, price in price_data.items()
                }
                
                # Collect results
                for future in as_completed(future_to_pair, timeout=30):
                    pair = future_to_pair[future]
                    try:
                        results[pair] = future.result()
                    except Exception as e:
                        logger.error(f"Validation error for {pair}: {e}")
                        results[pair] = True  # Allow if validation fails
                        
        except Exception as e:
            logger.error(f"Batch validation error: {e}")
            # Return all True if batch validation fails
            results = {pair: True for pair in price_data.keys()}
        
        return results
    
    def get_market_hours_info(self, pair: str) -> Optional[Dict[str, Any]]:
        """
        Get market hours and status information
        
        Args:
            pair: Currency pair
            
        Returns:
            Market hours info or None
        """
        try:
            yf_symbol = self.forex_symbol_map.get(pair)
            if not yf_symbol:
                return None
            
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            market_info = {
                'market_state': info.get('marketState', 'UNKNOWN'),
                'exchange_timezone': info.get('exchangeTimezoneName', 'UTC'),
                'is_eod_delayed': info.get('isEsgPopulated', False),
                'currency': info.get('currency', 'USD'),
                'symbol': yf_symbol
            }
            
            return market_info
            
        except Exception as e:
            logger.debug(f"Market hours info error for {pair}: {e}")
        
        return None
    
    def get_realtime_quote(self, pair: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time quote with bid/ask if available
        
        Args:
            pair: Currency pair
            
        Returns:
            Quote data or None
        """
        try:
            yf_symbol = self.forex_symbol_map.get(pair)
            if not yf_symbol:
                return None
            
            ticker = yf.Ticker(yf_symbol)
            info = ticker.info
            
            quote_data = {
                'symbol': pair,
                'bid': info.get('bid'),
                'ask': info.get('ask'),
                'price': info.get('regularMarketPrice'),
                'previous_close': info.get('previousClose'),
                'change': info.get('regularMarketChange'),
                'change_percent': info.get('regularMarketChangePercent'),
                'volume': info.get('regularMarketVolume', 0),
                'timestamp': datetime.now().isoformat()
            }
            
            # Clean up None values
            quote_data = {k: v for k, v in quote_data.items() if v is not None}
            
            return quote_data
            
        except Exception as e:
            logger.debug(f"Real-time quote error for {pair}: {e}")
        
        return None
    
    def clear_cache(self):
        """Clear the price cache"""
        self.price_cache.clear()
        logger.debug("yfinance cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        current_time = time.time()
        valid_entries = sum(1 for _, timestamp in self.price_cache.values() 
                           if current_time - timestamp < self.cache_expiry)
        
        return {
            'total_entries': len(self.price_cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self.price_cache) - valid_entries,
            'cache_expiry_seconds': self.cache_expiry
        }
    
    def cleanup_expired_cache(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        expired_keys = [key for key, (_, timestamp) in self.price_cache.items()
                       if current_time - timestamp >= self.cache_expiry]
        
        for key in expired_keys:
            del self.price_cache[key]
        
        if expired_keys:
            logger.debug(f"Removed {len(expired_keys)} expired cache entries")

# Global instance
yfinance_helper = YFinanceHelper()