"""
Extended Hours Monitor - Detect pre-market and after-hours activity

Monitors:
- Pre-market trading (4:00 AM - 9:30 AM ET)
- After-hours trading (4:00 PM - 8:00 PM ET)
- Significant price gaps from previous close
- Unusual extended hours volume
"""

import logging
from datetime import datetime, time as dt_time
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytz

from ..core.config import get_stock_settings
from ..data.models import (
    ExtendedHoursAlert,
    AlertSeverity,
    MarketSession,
)
from ..fetchers.stock_fetcher import StockDataFetcher

logger = logging.getLogger(__name__)


class ExtendedHoursMonitor:
    """Monitors pre-market and after-hours trading activity"""

    # Eastern timezone for market hours
    ET_TZ = pytz.timezone('US/Eastern')

    # Market session times (Eastern Time)
    PREMARKET_START = dt_time(4, 0)
    PREMARKET_END = dt_time(9, 30)
    REGULAR_START = dt_time(9, 30)
    REGULAR_END = dt_time(16, 0)
    AFTERHOURS_START = dt_time(16, 0)
    AFTERHOURS_END = dt_time(20, 0)

    def __init__(self, fetcher: Optional[StockDataFetcher] = None):
        """
        Initialize extended hours monitor

        Args:
            fetcher: Optional StockDataFetcher instance (creates new if not provided)
        """
        self.settings = get_stock_settings()
        self.fetcher = fetcher or StockDataFetcher()

        # Thresholds from settings
        self.price_change_threshold = self.settings.extended_hours_price_change_threshold
        self.volume_threshold = self.settings.extended_hours_volume_threshold

        logger.info(
            f"ExtendedHoursMonitor initialized: price_threshold={self.price_change_threshold}%, "
            f"volume_threshold={self.volume_threshold:,}"
        )

    def get_current_session(self) -> MarketSession:
        """
        Determine current market session based on Eastern Time

        Returns:
            MarketSession enum value
        """
        now = datetime.now(self.ET_TZ)
        current_time = now.time()

        # Check if weekend
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return MarketSession.CLOSED

        if self.PREMARKET_START <= current_time < self.PREMARKET_END:
            return MarketSession.PREMARKET
        elif self.REGULAR_START <= current_time < self.REGULAR_END:
            return MarketSession.REGULAR
        elif self.AFTERHOURS_START <= current_time < self.AFTERHOURS_END:
            return MarketSession.AFTERHOURS
        else:
            return MarketSession.CLOSED

    def is_extended_hours(self) -> bool:
        """Check if currently in extended hours trading session"""
        session = self.get_current_session()
        return session in (MarketSession.PREMARKET, MarketSession.AFTERHOURS)

    def analyze_symbol(self, symbol: str) -> Optional[ExtendedHoursAlert]:
        """
        Analyze a single symbol for extended hours activity

        Args:
            symbol: Stock ticker symbol

        Returns:
            ExtendedHoursAlert if significant activity detected, None otherwise
        """
        try:
            # Get extended hours quote
            quote = self.fetcher.get_extended_hours_quote(symbol)

            if not quote:
                # Fallback to regular quote
                quote = self.fetcher.get_quote(symbol)
                if not quote:
                    return None

            # Determine session
            session = self.get_current_session()
            if session == MarketSession.REGULAR:
                # During regular hours, check for potential gap setup
                return self._check_gap_setup(symbol, quote)
            elif session == MarketSession.CLOSED:
                logger.debug(f"Market closed, skipping {symbol}")
                return None

            # Get previous close for comparison
            prev_close = quote.previous_close
            if not prev_close:
                # Try to get from historical
                historical = self.fetcher.get_historical_data(symbol, days=2)
                if historical and len(historical) >= 2:
                    prev_close = historical[-2].close

            if not prev_close or prev_close == 0:
                logger.debug(f"{symbol}: No previous close available")
                return None

            # Calculate change from previous close
            current_price = quote.price
            price_change = current_price - prev_close
            price_change_pct = (price_change / prev_close) * 100

            # Check if change exceeds threshold
            if abs(price_change_pct) < self.price_change_threshold:
                logger.debug(
                    f"{symbol}: Extended hours change {price_change_pct:.2f}% "
                    f"below threshold {self.price_change_threshold}%"
                )
                return None

            # Determine severity
            severity = self._determine_severity(price_change_pct, quote.volume or 0)

            # Calculate spread if available
            spread_pct = None
            if quote.bid and quote.ask and quote.bid > 0:
                spread_pct = ((quote.ask - quote.bid) / quote.bid) * 100

            # Create alert
            alert = ExtendedHoursAlert(
                symbol=symbol,
                alert_type="EXTENDED_HOURS",
                severity=severity,
                session=session,
                current_price=current_price,
                regular_close=prev_close,
                price_change=price_change,
                price_change_percent=round(price_change_pct, 2),
                extended_volume=quote.volume or 0,
                bid=quote.bid,
                ask=quote.ask,
                spread_percent=round(spread_pct, 2) if spread_pct else None,
                catalyst=self._guess_catalyst(symbol, price_change_pct),
                timestamp=datetime.now(),
                source="extended_hours_monitor"
            )

            logger.info(
                f"Extended hours alert for {symbol}: {price_change_pct:+.2f}% in "
                f"{session.value}, severity={severity.value}"
            )

            return alert

        except Exception as e:
            logger.error(f"Error analyzing extended hours for {symbol}: {e}")
            return None

    def _determine_severity(self, price_change_pct: float, volume: int) -> AlertSeverity:
        """
        Determine alert severity based on price change and volume

        Args:
            price_change_pct: Percentage price change
            volume: Extended hours volume

        Returns:
            AlertSeverity level
        """
        abs_change = abs(price_change_pct)

        # Base severity on price change
        if abs_change >= 10:
            severity = AlertSeverity.CRITICAL
        elif abs_change >= 5:
            severity = AlertSeverity.HIGH
        elif abs_change >= self.price_change_threshold * 1.5:
            severity = AlertSeverity.MEDIUM
        else:
            severity = AlertSeverity.LOW

        # Upgrade if volume is significant
        if volume >= self.volume_threshold * 3:
            if severity == AlertSeverity.LOW:
                severity = AlertSeverity.MEDIUM
            elif severity == AlertSeverity.MEDIUM:
                severity = AlertSeverity.HIGH
        elif volume >= self.volume_threshold * 2:
            if severity == AlertSeverity.LOW:
                severity = AlertSeverity.MEDIUM

        return severity

    def _guess_catalyst(self, symbol: str, price_change_pct: float) -> Optional[str]:
        """
        Make an educated guess about the catalyst for the move

        In a real system, this would check news feeds, earnings calendar, etc.

        Args:
            symbol: Stock ticker
            price_change_pct: Price change percentage

        Returns:
            Possible catalyst string or None
        """
        # This is a placeholder - in production, integrate with news API
        # For now, return generic suggestions based on move size

        abs_change = abs(price_change_pct)

        if abs_change >= 10:
            return "Major news event (check news feeds)"
        elif abs_change >= 5:
            return "Possible earnings/guidance or significant news"
        elif abs_change >= 3:
            return "News or sector movement"

        return None

    def _check_gap_setup(self, symbol: str, quote) -> Optional[ExtendedHoursAlert]:
        """
        Check for potential gap setup during regular hours

        This identifies stocks that might gap up/down based on current movement
        """
        # For now, return None during regular hours
        # This could be expanded to identify stocks likely to gap
        return None

    def scan_watchlist(
        self,
        symbols: Optional[List[str]] = None,
        max_workers: int = 5
    ) -> List[ExtendedHoursAlert]:
        """
        Scan a list of symbols for extended hours activity

        Args:
            symbols: List of symbols to scan (uses default watchlist if None)
            max_workers: Number of concurrent workers

        Returns:
            List of ExtendedHoursAlert objects
        """
        session = self.get_current_session()

        if session not in (MarketSession.PREMARKET, MarketSession.AFTERHOURS):
            logger.info(f"Current session is {session.value}, skipping extended hours scan")
            return []

        if symbols is None:
            symbols = self.settings.default_watchlist

        logger.info(
            f"Scanning {len(symbols)} symbols for {session.value} activity..."
        )

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

        # Sort by absolute price change
        alerts.sort(key=lambda a: abs(a.price_change_percent), reverse=True)

        logger.info(
            f"Extended hours scan complete: {len(alerts)} alerts from {len(symbols)} symbols"
        )

        return alerts

    def get_movers(
        self,
        symbols: Optional[List[str]] = None,
        direction: str = "both",
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top movers in extended hours

        Args:
            symbols: List of symbols to check (uses default watchlist if None)
            direction: "up", "down", or "both"
            top_n: Number of results to return

        Returns:
            List of dicts with mover information
        """
        if symbols is None:
            symbols = self.settings.default_watchlist

        movers = []

        for symbol in symbols:
            try:
                quote = self.fetcher.get_extended_hours_quote(symbol)
                if not quote:
                    quote = self.fetcher.get_quote(symbol)

                if not quote or not quote.previous_close:
                    continue

                price_change = quote.price - quote.previous_close
                price_change_pct = (price_change / quote.previous_close) * 100

                # Filter by direction
                if direction == "up" and price_change_pct <= 0:
                    continue
                elif direction == "down" and price_change_pct >= 0:
                    continue

                movers.append({
                    "symbol": symbol,
                    "price": quote.price,
                    "previous_close": quote.previous_close,
                    "change": price_change,
                    "change_percent": round(price_change_pct, 2),
                    "volume": quote.volume or 0,
                    "session": self.get_current_session().value,
                    "source": quote.source
                })

            except Exception as e:
                logger.warning(f"Error getting mover data for {symbol}: {e}")

        # Sort by absolute percentage change
        if direction == "up":
            movers.sort(key=lambda x: x["change_percent"], reverse=True)
        elif direction == "down":
            movers.sort(key=lambda x: x["change_percent"])
        else:
            movers.sort(key=lambda x: abs(x["change_percent"]), reverse=True)

        return movers[:top_n]

    def monitor_gaps(
        self,
        symbols: Optional[List[str]] = None,
        min_gap_percent: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Monitor for potential gap scenarios

        Identifies stocks with significant extended hours moves that
        will likely gap at market open

        Args:
            symbols: List of symbols to monitor
            min_gap_percent: Minimum gap percentage to report

        Returns:
            List of potential gap scenarios
        """
        session = self.get_current_session()

        if session not in (MarketSession.PREMARKET, MarketSession.AFTERHOURS):
            return []

        if symbols is None:
            symbols = self.settings.default_watchlist

        gaps = []

        for symbol in symbols:
            try:
                quote = self.fetcher.get_extended_hours_quote(symbol)
                if not quote:
                    continue

                prev_close = quote.previous_close
                if not prev_close:
                    continue

                gap_pct = ((quote.price - prev_close) / prev_close) * 100

                if abs(gap_pct) >= min_gap_percent:
                    gaps.append({
                        "symbol": symbol,
                        "previous_close": prev_close,
                        "current_price": quote.price,
                        "expected_gap_percent": round(gap_pct, 2),
                        "gap_direction": "UP" if gap_pct > 0 else "DOWN",
                        "extended_volume": quote.volume or 0,
                        "session": session.value,
                        "confidence": self._calculate_gap_confidence(gap_pct, quote.volume or 0)
                    })

            except Exception as e:
                logger.warning(f"Error checking gap for {symbol}: {e}")

        # Sort by absolute gap size
        gaps.sort(key=lambda x: abs(x["expected_gap_percent"]), reverse=True)

        return gaps

    def _calculate_gap_confidence(self, gap_pct: float, volume: int) -> str:
        """
        Calculate confidence level for gap prediction

        Args:
            gap_pct: Expected gap percentage
            volume: Extended hours volume

        Returns:
            Confidence level string
        """
        abs_gap = abs(gap_pct)

        # Higher volume = more confident
        if volume >= self.volume_threshold * 3:
            volume_factor = "high"
        elif volume >= self.volume_threshold:
            volume_factor = "medium"
        else:
            volume_factor = "low"

        # Larger gaps are more likely to stick
        if abs_gap >= 5 and volume_factor == "high":
            return "HIGH"
        elif abs_gap >= 3 and volume_factor in ("high", "medium"):
            return "MEDIUM"
        else:
            return "LOW"

    def get_session_summary(
        self,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get summary of extended hours session activity

        Args:
            symbols: List of symbols to analyze

        Returns:
            Dict with session summary statistics
        """
        session = self.get_current_session()

        if symbols is None:
            symbols = self.settings.default_watchlist

        up_count = 0
        down_count = 0
        unchanged_count = 0
        total_volume = 0
        biggest_gainer = None
        biggest_loser = None
        biggest_gainer_pct = 0
        biggest_loser_pct = 0

        for symbol in symbols:
            try:
                quote = self.fetcher.get_quote(symbol)
                if not quote:
                    continue

                change_pct = quote.change_percent

                if change_pct > 0.1:
                    up_count += 1
                    if change_pct > biggest_gainer_pct:
                        biggest_gainer_pct = change_pct
                        biggest_gainer = symbol
                elif change_pct < -0.1:
                    down_count += 1
                    if change_pct < biggest_loser_pct:
                        biggest_loser_pct = change_pct
                        biggest_loser = symbol
                else:
                    unchanged_count += 1

                total_volume += quote.volume or 0

            except Exception:
                continue

        total = up_count + down_count + unchanged_count

        return {
            "session": session.value,
            "timestamp": datetime.now(self.ET_TZ).isoformat(),
            "symbols_analyzed": total,
            "advancing": up_count,
            "declining": down_count,
            "unchanged": unchanged_count,
            "advance_decline_ratio": round(up_count / down_count, 2) if down_count > 0 else float('inf'),
            "total_volume": total_volume,
            "biggest_gainer": {
                "symbol": biggest_gainer,
                "change_percent": biggest_gainer_pct
            } if biggest_gainer else None,
            "biggest_loser": {
                "symbol": biggest_loser,
                "change_percent": biggest_loser_pct
            } if biggest_loser else None
        }
