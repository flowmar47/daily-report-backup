"""
Pydantic data models for structured data validation and serialization.
Ensures data consistency across the application.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator


class SignalType(str, Enum):
    """Enum for forex signal types."""
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"
    HOLD = "HOLD"


class OptionStrategy(str, Enum):
    """Enum for options trading strategies."""
    CALL = "CALL"
    PUT = "PUT"
    SPREAD = "SPREAD"
    STRADDLE = "STRADDLE"
    STRANGLE = "STRANGLE"
    IRON_CONDOR = "IRON_CONDOR"
    BUTTERFLY = "BUTTERFLY"


class ForexSignal(BaseModel):
    """Model for forex trading signals."""
    pair: str = Field(..., description="Currency pair (e.g., EUR/USD)")
    signal: SignalType = Field(..., description="Trading signal")
    entry_price: Optional[float] = Field(None, description="Entry price level")
    stop_loss: Optional[float] = Field(None, description="Stop loss level")
    take_profit: Optional[float] = Field(None, description="Take profit level")
    confidence: Optional[float] = Field(None, ge=0, le=100, description="Signal confidence percentage")
    timeframe: Optional[str] = Field(None, description="Trading timeframe")
    analysis: Optional[str] = Field(None, description="Technical analysis notes")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @validator('pair')
    def validate_pair(cls, v):
        """Validate currency pair format."""
        if '/' not in v or len(v.split('/')) != 2:
            raise ValueError('Currency pair must be in format XXX/YYY')
        return v.upper()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OptionsPlay(BaseModel):
    """Model for options trading plays."""
    ticker: str = Field(..., description="Stock ticker symbol")
    strategy: OptionStrategy = Field(..., description="Options strategy")
    strike: Optional[float] = Field(None, description="Strike price")
    expiration: Optional[str] = Field(None, description="Expiration date")
    entry_price: Optional[float] = Field(None, description="Entry price for the option")
    exit_price: Optional[float] = Field(None, description="Target exit price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    confidence: Optional[float] = Field(None, ge=0, le=100, description="Play confidence percentage")
    rationale: Optional[str] = Field(None, description="Trade rationale")
    risk_reward: Optional[str] = Field(None, description="Risk/reward ratio")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @validator('ticker')
    def validate_ticker(cls, v):
        """Validate and normalize ticker symbol."""
        return v.upper().strip()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EarningsRelease(BaseModel):
    """Model for earnings release information."""
    ticker: str = Field(..., description="Company ticker symbol")
    company_name: Optional[str] = Field(None, description="Company name")
    release_date: Optional[str] = Field(None, description="Earnings release date")
    release_time: Optional[str] = Field(None, description="Release time (BMO/AMC)")
    eps_estimate: Optional[float] = Field(None, description="EPS estimate")
    revenue_estimate: Optional[float] = Field(None, description="Revenue estimate")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @validator('ticker')
    def validate_ticker(cls, v):
        """Validate and normalize ticker symbol."""
        return v.upper().strip()


class Trade(BaseModel):
    """Model for executed trades."""
    symbol: str = Field(..., description="Trading symbol")
    action: str = Field(..., description="Trade action (BUY/SELL)")
    quantity: Optional[float] = Field(None, description="Trade quantity")
    price: Optional[float] = Field(None, description="Execution price")
    timestamp: Optional[datetime] = Field(None, description="Trade timestamp")
    profit_loss: Optional[float] = Field(None, description="P&L if closing trade")
    notes: Optional[str] = Field(None, description="Trade notes")
    
    @validator('action')
    def validate_action(cls, v):
        """Validate trade action."""
        valid_actions = ['BUY', 'SELL', 'BUY_TO_OPEN', 'SELL_TO_CLOSE', 'BUY_TO_CLOSE', 'SELL_TO_OPEN']
        v_upper = v.upper()
        if v_upper not in valid_actions:
            raise ValueError(f'Action must be one of {valid_actions}')
        return v_upper


class MarketData(BaseModel):
    """Model for general market data."""
    index: str = Field(..., description="Market index name")
    value: float = Field(..., description="Current value")
    change: Optional[float] = Field(None, description="Change amount")
    change_percent: Optional[float] = Field(None, description="Change percentage")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DailyReport(BaseModel):
    """Model for complete daily report data."""
    report_date: datetime = Field(default_factory=datetime.now)
    forex_signals: List[ForexSignal] = Field(default_factory=list)
    options_plays: List[OptionsPlay] = Field(default_factory=list)
    earnings_releases: List[EarningsRelease] = Field(default_factory=list)
    trades: List[Trade] = Field(default_factory=list)
    market_data: List[MarketData] = Field(default_factory=list)
    summary: Optional[str] = Field(None, description="Daily summary")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('forex_signals')
    def limit_forex_signals(cls, v):
        """Limit forex signals to prevent overwhelming reports."""
        max_signals = 20
        if len(v) > max_signals:
            # Sort by confidence if available, otherwise keep first N
            sorted_signals = sorted(v, key=lambda x: x.confidence or 0, reverse=True)
            return sorted_signals[:max_signals]
        return v
    
    @validator('options_plays')
    def limit_options_plays(cls, v):
        """Limit options plays to configured amount."""
        max_plays = 3
        if len(v) > max_plays:
            # Sort by confidence if available
            sorted_plays = sorted(v, key=lambda x: x.confidence or 0, reverse=True)
            return sorted_plays[:max_plays]
        return v
    
    def to_telegram_format(self) -> str:
        """Convert report to Telegram-friendly markdown format."""
        lines = []
        
        # Header
        lines.append(f"📊 *Daily Financial Report*")
        lines.append(f"📅 {self.report_date.strftime('%B %d, %Y')}")
        lines.append("")
        
        # Forex Signals
        if self.forex_signals:
            lines.append("💱 *FOREX SIGNALS*")
            lines.append("")
            for signal in self.forex_signals[:10]:  # Limit display
                emoji = "🟢" if signal.signal == SignalType.BUY else "🔴" if signal.signal == SignalType.SELL else "⚪"
                lines.append(f"{emoji} *{signal.pair}*: {signal.signal.value}")
                if signal.entry_price:
                    lines.append(f"   Entry: {signal.entry_price}")
                if signal.stop_loss and signal.take_profit:
                    lines.append(f"   SL: {signal.stop_loss} | TP: {signal.take_profit}")
                lines.append("")
        
        # Options Plays
        if self.options_plays:
            lines.append("📈 *OPTIONS PLAYS*")
            lines.append("")
            for i, play in enumerate(self.options_plays, 1):
                lines.append(f"*Play {i}: ${play.ticker}*")
                lines.append(f"Strategy: {play.strategy.value}")
                if play.strike:
                    lines.append(f"Strike: ${play.strike}")
                if play.expiration:
                    lines.append(f"Expiration: {play.expiration}")
                if play.rationale:
                    lines.append(f"Rationale: {play.rationale[:100]}...")
                lines.append("")
        
        # Summary
        if self.summary:
            lines.append("📝 *SUMMARY*")
            lines.append(self.summary)
        
        return "\n".join(lines)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ScraperResult(BaseModel):
    """Model for scraper operation results."""
    success: bool = Field(..., description="Whether scraping was successful")
    data: Optional[DailyReport] = Field(None, description="Scraped data if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    duration: Optional[float] = Field(None, description="Operation duration in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }