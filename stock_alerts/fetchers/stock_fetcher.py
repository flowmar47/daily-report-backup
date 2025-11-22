"""
Stock Data Fetcher - Multi-source API integration for stock data

Supports:
- Alpha Vantage (TIME_SERIES_INTRADAY, GLOBAL_QUOTE)
- Twelve Data (time_series, quote)
- Finnhub (quote, candles)
- Polygon.io (aggregates, snapshot)
- yfinance (free, unlimited - fallback)

Implements intelligent fallback chain and rate limiting.
"""

import logging
import time
import pickle
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import defaultdict, deque
import threading

import requests

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

from ..core.config import get_stock_settings
from ..core.exceptions import DataFetchError, RateLimitError
from ..data.models import StockQuote, StockData, HistoricalBar, MarketSession

logger = logging.getLogger(__name__)


class RateLimitTracker:
    """Thread-safe rate limit tracking"""

    def __init__(self):
        self.call_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.daily_counts: Dict[str, int] = defaultdict(int)
        self.daily_reset: datetime = self._get_next_reset()
        self.lock = threading.Lock()

    def _get_next_reset(self) -> datetime:
        """Get next daily reset time (midnight)"""
        now = datetime.now()
        return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    def can_call(self, api_name: str, limit: int, period_seconds: int = 60) -> bool:
        """Check if we can make an API call"""
        with self.lock:
            now = datetime.now()

            # Reset daily counters if needed
            if now >= self.daily_reset:
                self.daily_counts.clear()
                self.daily_reset = self._get_next_reset()

            # Clean old calls
            cutoff = now - timedelta(seconds=period_seconds)
            while self.call_times[api_name] and self.call_times[api_name][0] < cutoff:
                self.call_times[api_name].popleft()

            return len(self.call_times[api_name]) < limit

    def record_call(self, api_name: str):
        """Record an API call"""
        with self.lock:
            self.call_times[api_name].append(datetime.now())
            self.daily_counts[api_name] += 1


class StockDataFetcher:
    """Multi-source stock data fetcher with intelligent fallbacks"""

    def __init__(self):
        self.settings = get_stock_settings()
        self.rate_limiter = RateLimitTracker()

        # Cache setup
        self.cache_dir = Path("cache/stock_data")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.quote_cache: Dict[str, Dict] = {}
        self.historical_cache: Dict[str, Dict] = self._load_cache()

        # API priority order (try in this order)
        self.api_priority = self._determine_api_priority()

        # Request session with retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'StockAlerts/1.0'
        })

        logger.info(f"StockDataFetcher initialized with APIs: {self.api_priority}")

    def _determine_api_priority(self) -> List[str]:
        """Determine API priority based on configured keys"""
        priority = []

        # yfinance is always available and free (use as primary fallback)
        if YFINANCE_AVAILABLE:
            priority.append('yfinance')

        # Add configured APIs in order of preference
        if self.settings.finnhub_api_key:
            priority.insert(0, 'finnhub')  # Fast, good for quotes

        if self.settings.alpha_vantage_api_key:
            priority.append('alpha_vantage')  # Good for historical

        if self.settings.twelve_data_api_key:
            priority.append('twelve_data')

        if self.settings.polygon_api_key:
            priority.append('polygon')

        return priority if priority else ['yfinance']

    def _load_cache(self) -> Dict:
        """Load historical cache from disk"""
        cache_file = self.cache_dir / "historical_cache.pkl"
        try:
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.warning(f"Could not load cache: {e}")
        return {}

    def _save_cache(self):
        """Save historical cache to disk"""
        cache_file = self.cache_dir / "historical_cache.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self.historical_cache, f)
        except Exception as e:
            logger.error(f"Could not save cache: {e}")

    def _is_cache_valid(self, cache_entry: Dict, ttl_seconds: int) -> bool:
        """Check if cache entry is still valid"""
        try:
            cached_time = cache_entry.get('cached_at')
            if isinstance(cached_time, str):
                cached_time = datetime.fromisoformat(cached_time)
            return datetime.now() - cached_time < timedelta(seconds=ttl_seconds)
        except Exception:
            return False

    def get_quote(self, symbol: str) -> Optional[StockQuote]:
        """
        Get real-time quote for a stock symbol

        Uses fallback chain: finnhub -> alpha_vantage -> twelve_data -> yfinance
        """
        symbol = symbol.upper().strip()

        # Check quote cache first
        cache_key = f"quote_{symbol}"
        if cache_key in self.quote_cache:
            if self._is_cache_valid(self.quote_cache[cache_key], self.settings.cache_ttl_quote):
                logger.debug(f"Using cached quote for {symbol}")
                return self.quote_cache[cache_key].get('data')

        # Try each API in priority order
        for api in self.api_priority:
            try:
                quote = self._fetch_quote_from_api(symbol, api)
                if quote:
                    # Cache the result
                    self.quote_cache[cache_key] = {
                        'data': quote,
                        'cached_at': datetime.now()
                    }
                    logger.info(f"Got quote for {symbol} from {api}")
                    return quote
            except RateLimitError as e:
                logger.warning(f"Rate limit hit on {api}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error fetching quote from {api}: {e}")
                continue

        logger.error(f"Could not fetch quote for {symbol} from any source")
        return None

    def _fetch_quote_from_api(self, symbol: str, api: str) -> Optional[StockQuote]:
        """Fetch quote from specific API"""
        if api == 'finnhub':
            return self._fetch_finnhub_quote(symbol)
        elif api == 'alpha_vantage':
            return self._fetch_alpha_vantage_quote(symbol)
        elif api == 'twelve_data':
            return self._fetch_twelve_data_quote(symbol)
        elif api == 'polygon':
            return self._fetch_polygon_quote(symbol)
        elif api == 'yfinance':
            return self._fetch_yfinance_quote(symbol)
        return None

    def _fetch_finnhub_quote(self, symbol: str) -> Optional[StockQuote]:
        """Fetch quote from Finnhub API"""
        if not self.rate_limiter.can_call('finnhub', self.settings.finnhub_rate_limit):
            raise RateLimitError("Finnhub rate limit exceeded")

        api_key = self.settings.finnhub_api_key
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"

        response = self.session.get(url, timeout=10)
        self.rate_limiter.record_call('finnhub')

        if response.status_code != 200:
            raise DataFetchError(f"Finnhub returned {response.status_code}")

        data = response.json()
        if not data or data.get('c', 0) == 0:
            return None

        return StockQuote(
            symbol=symbol,
            price=data.get('c', 0),
            change=data.get('d', 0),
            change_percent=data.get('dp', 0),
            high=data.get('h'),
            low=data.get('l'),
            open=data.get('o'),
            previous_close=data.get('pc'),
            timestamp=datetime.now(),
            source='finnhub'
        )

    def _fetch_alpha_vantage_quote(self, symbol: str) -> Optional[StockQuote]:
        """Fetch quote from Alpha Vantage API"""
        if not self.rate_limiter.can_call('alpha_vantage', 5):  # 5 per minute
            raise RateLimitError("Alpha Vantage rate limit exceeded")

        api_key = self.settings.alpha_vantage_api_key
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"

        response = self.session.get(url, timeout=15)
        self.rate_limiter.record_call('alpha_vantage')

        if response.status_code != 200:
            raise DataFetchError(f"Alpha Vantage returned {response.status_code}")

        data = response.json()
        quote_data = data.get('Global Quote', {})

        if not quote_data:
            return None

        price = float(quote_data.get('05. price', 0))
        if price == 0:
            return None

        change = float(quote_data.get('09. change', 0))
        change_pct = quote_data.get('10. change percent', '0%')
        change_pct = float(change_pct.replace('%', ''))

        return StockQuote(
            symbol=symbol,
            price=price,
            change=change,
            change_percent=change_pct,
            high=float(quote_data.get('03. high', 0)) or None,
            low=float(quote_data.get('04. low', 0)) or None,
            open=float(quote_data.get('02. open', 0)) or None,
            previous_close=float(quote_data.get('08. previous close', 0)) or None,
            volume=int(quote_data.get('06. volume', 0)),
            timestamp=datetime.now(),
            source='alpha_vantage'
        )

    def _fetch_twelve_data_quote(self, symbol: str) -> Optional[StockQuote]:
        """Fetch quote from Twelve Data API"""
        if not self.rate_limiter.can_call('twelve_data', 8):  # 8 per minute
            raise RateLimitError("Twelve Data rate limit exceeded")

        api_key = self.settings.twelve_data_api_key
        url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={api_key}"

        response = self.session.get(url, timeout=10)
        self.rate_limiter.record_call('twelve_data')

        if response.status_code != 200:
            raise DataFetchError(f"Twelve Data returned {response.status_code}")

        data = response.json()
        if data.get('status') == 'error' or not data.get('close'):
            return None

        return StockQuote(
            symbol=symbol,
            price=float(data.get('close', 0)),
            change=float(data.get('change', 0)),
            change_percent=float(data.get('percent_change', 0)),
            high=float(data.get('high', 0)) or None,
            low=float(data.get('low', 0)) or None,
            open=float(data.get('open', 0)) or None,
            previous_close=float(data.get('previous_close', 0)) or None,
            volume=int(data.get('volume', 0)),
            avg_volume=int(data.get('average_volume', 0)) or None,
            fifty_two_week_high=float(data.get('fifty_two_week', {}).get('high', 0)) or None,
            fifty_two_week_low=float(data.get('fifty_two_week', {}).get('low', 0)) or None,
            timestamp=datetime.now(),
            source='twelve_data'
        )

    def _fetch_polygon_quote(self, symbol: str) -> Optional[StockQuote]:
        """Fetch quote from Polygon.io API"""
        if not self.rate_limiter.can_call('polygon', self.settings.polygon_rate_limit):
            raise RateLimitError("Polygon rate limit exceeded")

        api_key = self.settings.polygon_api_key
        url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}?apiKey={api_key}"

        response = self.session.get(url, timeout=10)
        self.rate_limiter.record_call('polygon')

        if response.status_code != 200:
            raise DataFetchError(f"Polygon returned {response.status_code}")

        data = response.json()
        ticker = data.get('ticker', {})

        if not ticker:
            return None

        day = ticker.get('day', {})
        prev_day = ticker.get('prevDay', {})

        price = day.get('c', 0) or ticker.get('lastTrade', {}).get('p', 0)
        if not price:
            return None

        prev_close = prev_day.get('c', 0)
        change = price - prev_close if prev_close else 0
        change_pct = (change / prev_close * 100) if prev_close else 0

        return StockQuote(
            symbol=symbol,
            price=price,
            change=change,
            change_percent=change_pct,
            high=day.get('h'),
            low=day.get('l'),
            open=day.get('o'),
            previous_close=prev_close or None,
            volume=int(day.get('v', 0)),
            timestamp=datetime.now(),
            source='polygon'
        )

    def _fetch_yfinance_quote(self, symbol: str) -> Optional[StockQuote]:
        """Fetch quote from yfinance (free, unlimited)"""
        if not YFINANCE_AVAILABLE:
            return None

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.fast_info

            price = info.get('lastPrice', 0) or info.get('regularMarketPrice', 0)
            if not price:
                return None

            prev_close = info.get('previousClose', 0) or info.get('regularMarketPreviousClose', 0)
            change = price - prev_close if prev_close else 0
            change_pct = (change / prev_close * 100) if prev_close else 0

            return StockQuote(
                symbol=symbol,
                price=price,
                change=change,
                change_percent=change_pct,
                high=info.get('dayHigh') or info.get('regularMarketDayHigh'),
                low=info.get('dayLow') or info.get('regularMarketDayLow'),
                open=info.get('open') or info.get('regularMarketOpen'),
                previous_close=prev_close or None,
                volume=int(info.get('volume', 0) or info.get('regularMarketVolume', 0)),
                market_cap=info.get('marketCap'),
                timestamp=datetime.now(),
                source='yfinance'
            )
        except Exception as e:
            logger.warning(f"yfinance error for {symbol}: {e}")
            return None

    def get_historical_data(
        self,
        symbol: str,
        days: int = 20,
        interval: str = 'daily'
    ) -> List[HistoricalBar]:
        """
        Get historical OHLCV data

        Args:
            symbol: Stock ticker symbol
            days: Number of days of history
            interval: 'daily', '1hour', '15min', etc.

        Returns:
            List of HistoricalBar objects
        """
        symbol = symbol.upper().strip()
        cache_key = f"hist_{symbol}_{days}_{interval}"

        # Check cache
        if cache_key in self.historical_cache:
            if self._is_cache_valid(self.historical_cache[cache_key], self.settings.cache_ttl_historical):
                logger.debug(f"Using cached historical data for {symbol}")
                return self.historical_cache[cache_key].get('data', [])

        # Try each API
        for api in self.api_priority:
            try:
                bars = self._fetch_historical_from_api(symbol, days, interval, api)
                if bars:
                    # Cache and return
                    self.historical_cache[cache_key] = {
                        'data': bars,
                        'cached_at': datetime.now()
                    }
                    self._save_cache()
                    logger.info(f"Got {len(bars)} historical bars for {symbol} from {api}")
                    return bars
            except Exception as e:
                logger.warning(f"Error fetching historical from {api}: {e}")
                continue

        return []

    def _fetch_historical_from_api(
        self,
        symbol: str,
        days: int,
        interval: str,
        api: str
    ) -> List[HistoricalBar]:
        """Fetch historical data from specific API"""
        if api == 'yfinance':
            return self._fetch_yfinance_historical(symbol, days, interval)
        elif api == 'alpha_vantage':
            return self._fetch_alpha_vantage_historical(symbol, days, interval)
        elif api == 'polygon':
            return self._fetch_polygon_historical(symbol, days, interval)
        return []

    def _fetch_yfinance_historical(
        self,
        symbol: str,
        days: int,
        interval: str
    ) -> List[HistoricalBar]:
        """Fetch historical data from yfinance"""
        if not YFINANCE_AVAILABLE:
            return []

        try:
            ticker = yf.Ticker(symbol)

            # Map interval to yfinance format
            interval_map = {
                'daily': '1d',
                '1hour': '1h',
                '15min': '15m',
                '5min': '5m',
            }
            yf_interval = interval_map.get(interval, '1d')

            # Determine period
            if yf_interval in ['1d']:
                period = f"{days}d"
            else:
                # For intraday, max is 60 days
                period = f"{min(days, 60)}d"

            df = ticker.history(period=period, interval=yf_interval)

            if df.empty:
                return []

            bars = []
            for idx, row in df.iterrows():
                bars.append(HistoricalBar(
                    timestamp=idx.to_pydatetime(),
                    open=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    close=row['Close'],
                    volume=int(row['Volume'])
                ))

            return bars
        except Exception as e:
            logger.warning(f"yfinance historical error: {e}")
            return []

    def _fetch_alpha_vantage_historical(
        self,
        symbol: str,
        days: int,
        interval: str
    ) -> List[HistoricalBar]:
        """Fetch historical data from Alpha Vantage"""
        if not self.rate_limiter.can_call('alpha_vantage', 5):
            raise RateLimitError("Alpha Vantage rate limit exceeded")

        api_key = self.settings.alpha_vantage_api_key

        if interval == 'daily':
            function = 'TIME_SERIES_DAILY'
            time_key = 'Time Series (Daily)'
        else:
            function = 'TIME_SERIES_INTRADAY'
            interval_map = {'1hour': '60min', '15min': '15min', '5min': '5min'}
            av_interval = interval_map.get(interval, '60min')
            time_key = f'Time Series ({av_interval})'
            url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&interval={av_interval}&apikey={api_key}&outputsize=compact"

        if interval == 'daily':
            url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={api_key}&outputsize=compact"

        response = self.session.get(url, timeout=15)
        self.rate_limiter.record_call('alpha_vantage')

        if response.status_code != 200:
            raise DataFetchError(f"Alpha Vantage returned {response.status_code}")

        data = response.json()
        time_series = data.get(time_key, {})

        if not time_series:
            # Try alternative key format
            for key in data.keys():
                if 'Time Series' in key:
                    time_series = data[key]
                    break

        if not time_series:
            return []

        bars = []
        for date_str, values in list(time_series.items())[:days]:
            try:
                bars.append(HistoricalBar(
                    timestamp=datetime.fromisoformat(date_str.replace(' ', 'T')),
                    open=float(values.get('1. open', 0)),
                    high=float(values.get('2. high', 0)),
                    low=float(values.get('3. low', 0)),
                    close=float(values.get('4. close', 0)),
                    volume=int(values.get('5. volume', 0))
                ))
            except Exception:
                continue

        return sorted(bars, key=lambda x: x.timestamp)

    def _fetch_polygon_historical(
        self,
        symbol: str,
        days: int,
        interval: str
    ) -> List[HistoricalBar]:
        """Fetch historical data from Polygon.io"""
        if not self.rate_limiter.can_call('polygon', self.settings.polygon_rate_limit):
            raise RateLimitError("Polygon rate limit exceeded")

        api_key = self.settings.polygon_api_key

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Map interval
        multiplier = 1
        timespan = 'day'
        if interval == '1hour':
            timespan = 'hour'
        elif interval == '15min':
            multiplier = 15
            timespan = 'minute'
        elif interval == '5min':
            multiplier = 5
            timespan = 'minute'

        url = (
            f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/"
            f"{multiplier}/{timespan}/{start_date.strftime('%Y-%m-%d')}/"
            f"{end_date.strftime('%Y-%m-%d')}?apiKey={api_key}&limit={days * 10}"
        )

        response = self.session.get(url, timeout=15)
        self.rate_limiter.record_call('polygon')

        if response.status_code != 200:
            raise DataFetchError(f"Polygon returned {response.status_code}")

        data = response.json()
        results = data.get('results', [])

        if not results:
            return []

        bars = []
        for bar in results:
            try:
                bars.append(HistoricalBar(
                    timestamp=datetime.fromtimestamp(bar['t'] / 1000),
                    open=bar['o'],
                    high=bar['h'],
                    low=bar['l'],
                    close=bar['c'],
                    volume=int(bar['v']),
                    vwap=bar.get('vw')
                ))
            except Exception:
                continue

        return bars

    def get_stock_data(self, symbol: str) -> Optional[StockData]:
        """
        Get comprehensive stock data including quote and historical

        Args:
            symbol: Stock ticker symbol

        Returns:
            StockData object with quote, historical, and calculated metrics
        """
        symbol = symbol.upper().strip()

        # Get quote
        quote = self.get_quote(symbol)
        if not quote:
            return None

        # Get historical data
        historical = self.get_historical_data(symbol, days=30, interval='daily')

        # Calculate average volumes
        avg_20d = None
        avg_10d = None
        if len(historical) >= 10:
            volumes = [bar.volume for bar in historical[-20:] if bar.volume > 0]
            if len(volumes) >= 10:
                avg_20d = sum(volumes[-20:]) / len(volumes[-20:])
                avg_10d = sum(volumes[-10:]) / len(volumes[-10:])

        # Calculate volatility (20-day)
        volatility = None
        if len(historical) >= 20:
            closes = [bar.close for bar in historical[-20:]]
            if closes:
                import statistics
                try:
                    returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
                    volatility = statistics.stdev(returns) * 100  # As percentage
                except Exception:
                    pass

        # Calculate simple RSI
        rsi = self._calculate_rsi(historical)

        # Calculate support/resistance
        support, resistance = self._calculate_support_resistance(historical)

        return StockData(
            symbol=symbol,
            quote=quote,
            historical=historical,
            avg_volume_20d=avg_20d,
            avg_volume_10d=avg_10d,
            volatility_20d=volatility,
            rsi_14=rsi,
            support_level=support,
            resistance_level=resistance
        )

    def _calculate_rsi(self, bars: List[HistoricalBar], period: int = 14) -> Optional[float]:
        """Calculate RSI from historical bars"""
        if len(bars) < period + 1:
            return None

        closes = [bar.close for bar in bars]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]

        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    def _calculate_support_resistance(
        self,
        bars: List[HistoricalBar],
        lookback: int = 20
    ) -> tuple[Optional[float], Optional[float]]:
        """Calculate simple support and resistance levels"""
        if len(bars) < lookback:
            return None, None

        recent_bars = bars[-lookback:]
        lows = [bar.low for bar in recent_bars]
        highs = [bar.high for bar in recent_bars]

        support = min(lows)
        resistance = max(highs)

        return support, resistance

    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Optional[StockQuote]]:
        """
        Get quotes for multiple symbols

        Args:
            symbols: List of stock symbols

        Returns:
            Dict mapping symbol to quote (or None if failed)
        """
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_quote(symbol)
            # Small delay to respect rate limits
            time.sleep(0.1)
        return results

    def get_extended_hours_quote(self, symbol: str) -> Optional[StockQuote]:
        """
        Get extended hours quote (pre-market or after-hours)

        Note: Not all APIs support extended hours data
        """
        symbol = symbol.upper().strip()

        # Finnhub doesn't distinguish extended hours in basic quote
        # Polygon has better extended hours support

        if 'polygon' in self.api_priority and self.settings.polygon_api_key:
            try:
                quote = self._fetch_polygon_quote(symbol)
                if quote:
                    # Determine session based on time
                    now = datetime.now()
                    hour = now.hour

                    if hour < 9 or (hour == 9 and now.minute < 30):
                        quote.session = MarketSession.PREMARKET
                    elif hour >= 16:
                        quote.session = MarketSession.AFTERHOURS
                    else:
                        quote.session = MarketSession.REGULAR

                    return quote
            except Exception as e:
                logger.warning(f"Could not get extended hours quote from Polygon: {e}")

        # Fallback to yfinance
        if YFINANCE_AVAILABLE:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info

                # yfinance provides pre/post market prices when available
                pre_price = info.get('preMarketPrice')
                post_price = info.get('postMarketPrice')
                regular_price = info.get('regularMarketPrice', 0)

                now = datetime.now()
                hour = now.hour

                if hour < 9 and pre_price:
                    return StockQuote(
                        symbol=symbol,
                        price=pre_price,
                        change=pre_price - regular_price,
                        change_percent=((pre_price - regular_price) / regular_price * 100) if regular_price else 0,
                        previous_close=regular_price,
                        session=MarketSession.PREMARKET,
                        source='yfinance'
                    )
                elif hour >= 16 and post_price:
                    return StockQuote(
                        symbol=symbol,
                        price=post_price,
                        change=post_price - regular_price,
                        change_percent=((post_price - regular_price) / regular_price * 100) if regular_price else 0,
                        previous_close=regular_price,
                        session=MarketSession.AFTERHOURS,
                        source='yfinance'
                    )
            except Exception as e:
                logger.warning(f"Could not get extended hours from yfinance: {e}")

        return None
