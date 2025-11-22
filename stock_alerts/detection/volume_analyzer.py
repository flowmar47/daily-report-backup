"""
Volume Analyzer - Detect unusual trading volume patterns

Identifies:
- Unusual volume spikes (relative to historical average)
- Volume breakouts with price action confirmation
- Accumulation/distribution patterns
- Sector-wide volume anomalies
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.config import get_stock_settings
from ..data.models import (
    StockData,
    VolumeAlert,
    AlertSeverity,
    MarketSession,
)
from ..fetchers.stock_fetcher import StockDataFetcher

logger = logging.getLogger(__name__)


class VolumeAnalyzer:
    """Analyzes trading volume for unusual activity patterns"""

    def __init__(self, fetcher: Optional[StockDataFetcher] = None):
        """
        Initialize volume analyzer

        Args:
            fetcher: Optional StockDataFetcher instance (creates new if not provided)
        """
        self.settings = get_stock_settings()
        self.fetcher = fetcher or StockDataFetcher()

        # Thresholds from settings
        self.unusual_threshold = self.settings.unusual_volume_threshold
        self.extreme_threshold = self.settings.extreme_volume_threshold
        self.min_volume = self.settings.min_volume_for_alert
        self.lookback_days = self.settings.volume_lookback_days

        logger.info(
            f"VolumeAnalyzer initialized: unusual={self.unusual_threshold}x, "
            f"extreme={self.extreme_threshold}x, min_vol={self.min_volume:,}"
        )

    def analyze_symbol(self, symbol: str) -> Optional[VolumeAlert]:
        """
        Analyze a single symbol for unusual volume

        Args:
            symbol: Stock ticker symbol

        Returns:
            VolumeAlert if unusual activity detected, None otherwise
        """
        try:
            # Get comprehensive stock data
            stock_data = self.fetcher.get_stock_data(symbol)

            if not stock_data or not stock_data.quote:
                logger.debug(f"No data available for {symbol}")
                return None

            # Check if volume meets minimum threshold
            current_volume = stock_data.quote.volume
            if current_volume < self.min_volume:
                logger.debug(f"{symbol}: Volume {current_volume:,} below minimum {self.min_volume:,}")
                return None

            # Calculate volume ratio
            avg_volume = stock_data.avg_volume_20d
            if not avg_volume or avg_volume == 0:
                # Try to use quote's avg_volume
                avg_volume = stock_data.quote.avg_volume
                if not avg_volume or avg_volume == 0:
                    logger.debug(f"{symbol}: No average volume data available")
                    return None

            volume_ratio = current_volume / avg_volume

            # Determine if volume is unusual
            if volume_ratio < self.unusual_threshold:
                logger.debug(f"{symbol}: Volume ratio {volume_ratio:.2f}x below threshold {self.unusual_threshold}x")
                return None

            # Determine severity
            severity = self._determine_severity(volume_ratio, stock_data)

            # Generate context string
            context = self._generate_context(stock_data, volume_ratio)

            # Create alert
            alert = VolumeAlert(
                symbol=symbol,
                alert_type="UNUSUAL_VOLUME",
                severity=severity,
                current_volume=current_volume,
                avg_volume=avg_volume,
                volume_ratio=round(volume_ratio, 2),
                price=stock_data.quote.price,
                price_change=stock_data.quote.change,
                price_change_percent=stock_data.quote.change_percent,
                session=stock_data.quote.session,
                rsi=stock_data.rsi_14,
                support=stock_data.support_level,
                resistance=stock_data.resistance_level,
                context=context,
                timestamp=datetime.now(),
                source="volume_analyzer"
            )

            logger.info(
                f"Volume alert for {symbol}: {volume_ratio:.2f}x average, "
                f"severity={severity.value}"
            )

            return alert

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None

    def _determine_severity(self, volume_ratio: float, stock_data: StockData) -> AlertSeverity:
        """
        Determine alert severity based on volume ratio and other factors

        Args:
            volume_ratio: Current volume / average volume
            stock_data: Full stock data

        Returns:
            AlertSeverity level
        """
        # Base severity on volume ratio
        if volume_ratio >= self.extreme_threshold:
            base_severity = AlertSeverity.CRITICAL
        elif volume_ratio >= self.unusual_threshold * 2:
            base_severity = AlertSeverity.HIGH
        elif volume_ratio >= self.unusual_threshold * 1.5:
            base_severity = AlertSeverity.MEDIUM
        else:
            base_severity = AlertSeverity.LOW

        # Upgrade severity if price movement is significant
        price_change_pct = abs(stock_data.quote.change_percent)

        if price_change_pct > 5:
            # Significant price move with volume - upgrade
            if base_severity == AlertSeverity.LOW:
                base_severity = AlertSeverity.MEDIUM
            elif base_severity == AlertSeverity.MEDIUM:
                base_severity = AlertSeverity.HIGH
            elif base_severity == AlertSeverity.HIGH:
                base_severity = AlertSeverity.CRITICAL

        # Consider RSI extremes
        rsi = stock_data.rsi_14
        if rsi and (rsi < 30 or rsi > 70):
            # RSI at extreme with volume - potentially significant
            if base_severity == AlertSeverity.LOW:
                base_severity = AlertSeverity.MEDIUM

        return base_severity

    def _generate_context(self, stock_data: StockData, volume_ratio: float) -> str:
        """
        Generate context string explaining the alert

        Args:
            stock_data: Full stock data
            volume_ratio: Volume ratio

        Returns:
            Context string
        """
        contexts = []

        # Volume context
        if volume_ratio >= self.extreme_threshold:
            contexts.append("EXTREME volume spike")
        elif volume_ratio >= self.unusual_threshold * 2:
            contexts.append("Very high volume")
        else:
            contexts.append("Elevated volume")

        # Price action context
        price_change = stock_data.quote.change_percent
        if price_change > 3:
            contexts.append("strong upward price movement")
        elif price_change > 1:
            contexts.append("positive price action")
        elif price_change < -3:
            contexts.append("strong downward price movement")
        elif price_change < -1:
            contexts.append("negative price action")
        else:
            contexts.append("relatively flat price")

        # RSI context
        rsi = stock_data.rsi_14
        if rsi:
            if rsi > 70:
                contexts.append("RSI overbought")
            elif rsi < 30:
                contexts.append("RSI oversold")

        # Support/resistance context
        if stock_data.resistance_level and stock_data.quote.price >= stock_data.resistance_level * 0.98:
            contexts.append("near resistance")
        elif stock_data.support_level and stock_data.quote.price <= stock_data.support_level * 1.02:
            contexts.append("near support")

        return ", ".join(contexts)

    def scan_watchlist(
        self,
        symbols: Optional[List[str]] = None,
        max_workers: int = 5
    ) -> List[VolumeAlert]:
        """
        Scan a list of symbols for unusual volume

        Args:
            symbols: List of symbols to scan (uses default watchlist if None)
            max_workers: Number of concurrent workers

        Returns:
            List of VolumeAlert objects for symbols with unusual volume
        """
        if symbols is None:
            symbols = self.settings.default_watchlist

        logger.info(f"Scanning {len(symbols)} symbols for unusual volume...")

        alerts = []

        # Use thread pool for concurrent API calls
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.analyze_symbol, symbol): symbol
                for symbol in symbols
            }

            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    alert = future.result()
                    if alert:
                        alerts.append(alert)
                except Exception as e:
                    logger.error(f"Error scanning {symbol}: {e}")

        # Sort by severity and volume ratio
        alerts.sort(
            key=lambda a: (
                {
                    AlertSeverity.CRITICAL: 0,
                    AlertSeverity.HIGH: 1,
                    AlertSeverity.MEDIUM: 2,
                    AlertSeverity.LOW: 3
                }.get(a.severity, 4),
                -a.volume_ratio
            )
        )

        logger.info(f"Scan complete: {len(alerts)} alerts from {len(symbols)} symbols")

        return alerts

    def analyze_volume_breakout(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Analyze if current volume represents a breakout pattern

        A volume breakout is when:
        - Volume is significantly above average
        - Price is moving in direction of volume
        - Price is breaking through support/resistance

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dict with breakout analysis or None
        """
        stock_data = self.fetcher.get_stock_data(symbol)

        if not stock_data or not stock_data.quote:
            return None

        # Need historical data for breakout analysis
        if len(stock_data.historical) < 20:
            return None

        current_volume = stock_data.quote.volume
        avg_volume = stock_data.avg_volume_20d or 0

        if avg_volume == 0:
            return None

        volume_ratio = current_volume / avg_volume
        price = stock_data.quote.price
        price_change_pct = stock_data.quote.change_percent

        # Determine breakout type
        breakout_type = None
        breakout_level = None

        if stock_data.resistance_level and price > stock_data.resistance_level:
            if price_change_pct > 0 and volume_ratio >= self.unusual_threshold:
                breakout_type = "RESISTANCE_BREAKOUT"
                breakout_level = stock_data.resistance_level

        elif stock_data.support_level and price < stock_data.support_level:
            if price_change_pct < 0 and volume_ratio >= self.unusual_threshold:
                breakout_type = "SUPPORT_BREAKDOWN"
                breakout_level = stock_data.support_level

        if not breakout_type:
            return None

        return {
            "symbol": symbol,
            "breakout_type": breakout_type,
            "breakout_level": breakout_level,
            "current_price": price,
            "price_change_percent": price_change_pct,
            "volume_ratio": round(volume_ratio, 2),
            "rsi": stock_data.rsi_14,
            "timestamp": datetime.now().isoformat()
        }

    def get_volume_leaders(
        self,
        symbols: Optional[List[str]] = None,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top stocks by volume ratio

        Args:
            symbols: List of symbols to analyze (uses default watchlist if None)
            top_n: Number of top stocks to return

        Returns:
            List of dicts with symbol, volume ratio, and other data
        """
        if symbols is None:
            symbols = self.settings.default_watchlist

        results = []

        for symbol in symbols:
            try:
                quote = self.fetcher.get_quote(symbol)
                if not quote or not quote.volume:
                    continue

                avg_volume = quote.avg_volume
                if not avg_volume:
                    # Try to get from historical
                    historical = self.fetcher.get_historical_data(symbol, days=20)
                    if historical:
                        volumes = [b.volume for b in historical if b.volume > 0]
                        avg_volume = sum(volumes) / len(volumes) if volumes else None

                if not avg_volume or avg_volume == 0:
                    continue

                volume_ratio = quote.volume / avg_volume

                results.append({
                    "symbol": symbol,
                    "volume": quote.volume,
                    "avg_volume": avg_volume,
                    "volume_ratio": round(volume_ratio, 2),
                    "price": quote.price,
                    "change_percent": quote.change_percent,
                    "source": quote.source
                })

            except Exception as e:
                logger.warning(f"Error getting volume data for {symbol}: {e}")

        # Sort by volume ratio descending
        results.sort(key=lambda x: x["volume_ratio"], reverse=True)

        return results[:top_n]

    def detect_accumulation_distribution(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Detect accumulation or distribution patterns

        Accumulation: High volume on up days, low volume on down days
        Distribution: High volume on down days, low volume on up days

        Args:
            symbol: Stock ticker symbol

        Returns:
            Dict with accumulation/distribution analysis
        """
        stock_data = self.fetcher.get_stock_data(symbol)

        if not stock_data or len(stock_data.historical) < 10:
            return None

        # Analyze recent bars
        recent_bars = stock_data.historical[-10:]

        up_volume = 0
        down_volume = 0
        up_days = 0
        down_days = 0

        for i in range(1, len(recent_bars)):
            prev_close = recent_bars[i - 1].close
            curr_bar = recent_bars[i]

            if curr_bar.close > prev_close:
                up_volume += curr_bar.volume
                up_days += 1
            elif curr_bar.close < prev_close:
                down_volume += curr_bar.volume
                down_days += 1

        if up_days == 0 or down_days == 0:
            return None

        avg_up_volume = up_volume / up_days
        avg_down_volume = down_volume / down_days

        # Calculate accumulation/distribution ratio
        if avg_down_volume > 0:
            ad_ratio = avg_up_volume / avg_down_volume
        else:
            ad_ratio = float('inf') if avg_up_volume > 0 else 1.0

        # Determine pattern
        pattern = None
        if ad_ratio > 1.5:
            pattern = "ACCUMULATION"
        elif ad_ratio < 0.67:
            pattern = "DISTRIBUTION"
        else:
            pattern = "NEUTRAL"

        return {
            "symbol": symbol,
            "pattern": pattern,
            "ad_ratio": round(ad_ratio, 2) if ad_ratio != float('inf') else "INF",
            "avg_up_volume": int(avg_up_volume),
            "avg_down_volume": int(avg_down_volume),
            "up_days": up_days,
            "down_days": down_days,
            "current_price": stock_data.quote.price,
            "timestamp": datetime.now().isoformat()
        }
