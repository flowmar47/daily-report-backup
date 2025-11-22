"""Data models for stock alerts system"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class AlertSeverity(str, Enum):
    """Severity levels for alerts"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MarketSession(str, Enum):
    """Market session types"""
    PREMARKET = "PREMARKET"
    REGULAR = "REGULAR"
    AFTERHOURS = "AFTERHOURS"
    CLOSED = "CLOSED"


class StockQuote(BaseModel):
    """Real-time stock quote data"""
    symbol: str = Field(..., description="Stock ticker symbol")
    price: float = Field(..., gt=0, description="Current price")
    change: float = Field(default=0.0, description="Price change from previous close")
    change_percent: float = Field(default=0.0, description="Price change percentage")
    volume: int = Field(default=0, ge=0, description="Current volume")
    avg_volume: Optional[int] = Field(None, description="Average daily volume")
    high: Optional[float] = Field(None, description="Day high")
    low: Optional[float] = Field(None, description="Day low")
    open: Optional[float] = Field(None, description="Opening price")
    previous_close: Optional[float] = Field(None, description="Previous close")
    bid: Optional[float] = Field(None, description="Bid price")
    ask: Optional[float] = Field(None, description="Ask price")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    timestamp: datetime = Field(default_factory=datetime.now, description="Quote timestamp")
    source: str = Field(default="unknown", description="Data source")
    session: MarketSession = Field(default=MarketSession.REGULAR, description="Market session")

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and normalize stock symbol"""
        return v.upper().strip()

    @property
    def volume_ratio(self) -> Optional[float]:
        """Calculate volume ratio vs average"""
        if self.avg_volume and self.avg_volume > 0:
            return self.volume / self.avg_volume
        return None


class HistoricalBar(BaseModel):
    """Single bar of historical data"""
    timestamp: datetime = Field(..., description="Bar timestamp")
    open: float = Field(..., gt=0, description="Open price")
    high: float = Field(..., gt=0, description="High price")
    low: float = Field(..., gt=0, description="Low price")
    close: float = Field(..., gt=0, description="Close price")
    volume: int = Field(..., ge=0, description="Volume")
    vwap: Optional[float] = Field(None, description="Volume-weighted average price")


class StockData(BaseModel):
    """Comprehensive stock data with historical context"""
    symbol: str = Field(..., description="Stock ticker symbol")
    quote: StockQuote = Field(..., description="Current quote data")
    historical: List[HistoricalBar] = Field(default_factory=list, description="Historical bars")
    avg_volume_20d: Optional[float] = Field(None, description="20-day average volume")
    avg_volume_10d: Optional[float] = Field(None, description="10-day average volume")
    volatility_20d: Optional[float] = Field(None, description="20-day volatility (std dev)")
    rsi_14: Optional[float] = Field(None, description="14-period RSI")
    support_level: Optional[float] = Field(None, description="Recent support level")
    resistance_level: Optional[float] = Field(None, description="Recent resistance level")
    fifty_two_week_high: Optional[float] = Field(None, description="52-week high")
    fifty_two_week_low: Optional[float] = Field(None, description="52-week low")
    sector: Optional[str] = Field(None, description="Stock sector")
    industry: Optional[str] = Field(None, description="Stock industry")
    timestamp: datetime = Field(default_factory=datetime.now, description="Data timestamp")

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and normalize stock symbol"""
        return v.upper().strip()

    @property
    def volume_vs_avg(self) -> Optional[float]:
        """Calculate current volume vs 20-day average"""
        if self.avg_volume_20d and self.avg_volume_20d > 0:
            return self.quote.volume / self.avg_volume_20d
        return None

    @property
    def price_position_52w(self) -> Optional[float]:
        """Calculate price position within 52-week range (0-1)"""
        if self.fifty_two_week_high and self.fifty_two_week_low:
            range_size = self.fifty_two_week_high - self.fifty_two_week_low
            if range_size > 0:
                return (self.quote.price - self.fifty_two_week_low) / range_size
        return None


class VolumeAlert(BaseModel):
    """Alert for unusual volume activity"""
    symbol: str = Field(..., description="Stock ticker symbol")
    alert_type: str = Field(default="UNUSUAL_VOLUME", description="Alert type")
    severity: AlertSeverity = Field(..., description="Alert severity")
    current_volume: int = Field(..., description="Current trading volume")
    avg_volume: float = Field(..., description="Average volume for comparison")
    volume_ratio: float = Field(..., description="Current volume / average volume")
    price: float = Field(..., description="Current stock price")
    price_change: float = Field(default=0.0, description="Price change")
    price_change_percent: float = Field(default=0.0, description="Price change percentage")
    session: MarketSession = Field(default=MarketSession.REGULAR, description="Market session")
    rsi: Optional[float] = Field(None, description="Current RSI")
    support: Optional[float] = Field(None, description="Support level")
    resistance: Optional[float] = Field(None, description="Resistance level")
    context: Optional[str] = Field(None, description="Additional context")
    timestamp: datetime = Field(default_factory=datetime.now, description="Alert timestamp")
    source: str = Field(default="stock_alerts", description="Alert source")

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and normalize stock symbol"""
        return v.upper().strip()

    @property
    def direction(self) -> str:
        """Determine price direction"""
        if self.price_change_percent > 0.5:
            return "UP"
        elif self.price_change_percent < -0.5:
            return "DOWN"
        return "FLAT"

    def to_alert_message(self) -> str:
        """Format alert as message string"""
        direction_symbol = "+" if self.price_change >= 0 else ""
        severity_indicator = {
            AlertSeverity.LOW: "",
            AlertSeverity.MEDIUM: "[!]",
            AlertSeverity.HIGH: "[!!]",
            AlertSeverity.CRITICAL: "[!!!]"
        }

        lines = [
            f"{severity_indicator.get(self.severity, '')} {self.symbol} - UNUSUAL VOLUME",
            f"Price: ${self.price:.2f} ({direction_symbol}{self.price_change_percent:.2f}%)",
            f"Volume: {self.current_volume:,} ({self.volume_ratio:.1f}x average)",
        ]

        if self.rsi:
            lines.append(f"RSI(14): {self.rsi:.1f}")

        if self.context:
            lines.append(f"Context: {self.context}")

        return "\n".join(lines)


class ExtendedHoursAlert(BaseModel):
    """Alert for pre-market or after-hours activity"""
    symbol: str = Field(..., description="Stock ticker symbol")
    alert_type: str = Field(default="EXTENDED_HOURS", description="Alert type")
    severity: AlertSeverity = Field(..., description="Alert severity")
    session: MarketSession = Field(..., description="Pre-market or after-hours")
    current_price: float = Field(..., description="Current extended hours price")
    regular_close: float = Field(..., description="Regular session close price")
    price_change: float = Field(..., description="Change from regular close")
    price_change_percent: float = Field(..., description="Percentage change")
    extended_volume: int = Field(..., description="Extended hours volume")
    bid: Optional[float] = Field(None, description="Current bid")
    ask: Optional[float] = Field(None, description="Current ask")
    spread_percent: Optional[float] = Field(None, description="Bid-ask spread percentage")
    catalyst: Optional[str] = Field(None, description="Potential catalyst/reason")
    timestamp: datetime = Field(default_factory=datetime.now, description="Alert timestamp")
    source: str = Field(default="stock_alerts", description="Alert source")

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Validate and normalize stock symbol"""
        return v.upper().strip()

    @property
    def direction(self) -> str:
        """Determine price direction"""
        if self.price_change_percent > 0.5:
            return "UP"
        elif self.price_change_percent < -0.5:
            return "DOWN"
        return "FLAT"

    def to_alert_message(self) -> str:
        """Format alert as message string"""
        session_name = "PRE-MARKET" if self.session == MarketSession.PREMARKET else "AFTER-HOURS"
        direction_symbol = "+" if self.price_change >= 0 else ""
        severity_indicator = {
            AlertSeverity.LOW: "",
            AlertSeverity.MEDIUM: "[!]",
            AlertSeverity.HIGH: "[!!]",
            AlertSeverity.CRITICAL: "[!!!]"
        }

        lines = [
            f"{severity_indicator.get(self.severity, '')} {self.symbol} - {session_name} ALERT",
            f"Price: ${self.current_price:.2f} ({direction_symbol}{self.price_change_percent:.2f}% from close)",
            f"Regular Close: ${self.regular_close:.2f}",
            f"Extended Volume: {self.extended_volume:,}",
        ]

        if self.bid and self.ask:
            lines.append(f"Bid/Ask: ${self.bid:.2f} / ${self.ask:.2f}")

        if self.catalyst:
            lines.append(f"Catalyst: {self.catalyst}")

        return "\n".join(lines)


class AlertBatch(BaseModel):
    """Batch of alerts for messaging"""
    alerts: List[VolumeAlert | ExtendedHoursAlert] = Field(
        default_factory=list,
        description="List of alerts"
    )
    generated_at: datetime = Field(default_factory=datetime.now)
    batch_id: str = Field(default="", description="Unique batch identifier")

    @property
    def volume_alerts(self) -> List[VolumeAlert]:
        """Get only volume alerts"""
        return [a for a in self.alerts if isinstance(a, VolumeAlert)]

    @property
    def extended_hours_alerts(self) -> List[ExtendedHoursAlert]:
        """Get only extended hours alerts"""
        return [a for a in self.alerts if isinstance(a, ExtendedHoursAlert)]

    @property
    def critical_alerts(self) -> List[VolumeAlert | ExtendedHoursAlert]:
        """Get critical severity alerts"""
        return [a for a in self.alerts if a.severity == AlertSeverity.CRITICAL]

    def to_message(self, max_alerts: int = 10) -> str:
        """Format batch as message string"""
        if not self.alerts:
            return "No alerts to report."

        lines = [
            "STOCK ALERTS",
            f"Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Total Alerts: {len(self.alerts)}",
            "=" * 40,
        ]

        # Sort by severity (critical first)
        sorted_alerts = sorted(
            self.alerts,
            key=lambda a: {
                AlertSeverity.CRITICAL: 0,
                AlertSeverity.HIGH: 1,
                AlertSeverity.MEDIUM: 2,
                AlertSeverity.LOW: 3
            }.get(a.severity, 4)
        )

        for alert in sorted_alerts[:max_alerts]:
            lines.append("")
            lines.append(alert.to_alert_message())
            lines.append("-" * 40)

        if len(self.alerts) > max_alerts:
            lines.append(f"\n... and {len(self.alerts) - max_alerts} more alerts")

        return "\n".join(lines)
