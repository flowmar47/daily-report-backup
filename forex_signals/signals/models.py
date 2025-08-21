"""
Data models for forex signals using Pydantic for validation
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator


class SignalAction(str, Enum):
    """Signal action types"""
    BUY = "BUY"
    SELL = "SELL" 
    HOLD = "HOLD"


class SignalStrength(str, Enum):
    """Signal strength categories"""
    STRONG = "Strong"
    MEDIUM = "Medium"
    WEAK = "Weak"


class SignalComponent(BaseModel):
    """Individual signal component result"""
    component: str = Field(..., description="Component name (technical, economic, etc.)")
    score: float = Field(..., ge=-1.0, le=1.0, description="Component score (-1.0 to 1.0)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Component confidence (0.0 to 1.0)")
    weight: float = Field(..., ge=0.0, le=1.0, description="Component weight in overall signal")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional component details")
    
    @field_validator('component')
    @classmethod
    def validate_component_name(cls, v: str) -> str:
        """Validate component name"""
        valid_components = {'technical', 'economic', 'geopolitical', 'sentiment'}
        if v.lower() not in valid_components:
            raise ValueError(f"Component must be one of: {valid_components}")
        return v.lower()


class TradingSignal(BaseModel):
    """Complete trading signal with entry/exit targets and metadata"""
    pair: str = Field(..., min_length=6, max_length=6, description="Currency pair (e.g., EURUSD)")
    action: SignalAction = Field(..., description="Trading action")
    
    # Price information
    entry_price: Optional[float] = Field(None, gt=0, description="Entry price")
    exit_price: Optional[float] = Field(None, gt=0, description="Exit/target price") 
    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price")
    take_profit: Optional[float] = Field(None, gt=0, description="Take profit price")
    
    # Pip calculations
    target_pips: Optional[float] = Field(None, description="Target in pips")
    stop_loss_pips: Optional[float] = Field(None, description="Stop loss in pips")
    
    # Signal metadata
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall signal confidence")
    signal_strength: float = Field(..., ge=-1.0, le=1.0, description="Signal strength score") 
    strength_category: SignalStrength = Field(..., description="Signal strength category")
    
    # Risk metrics
    risk_reward_ratio: Optional[float] = Field(None, gt=0, description="Risk to reward ratio")
    weekly_achievement_probability: float = Field(..., ge=0.0, le=1.0, description="Probability of hitting target within week")
    
    # Timing
    expected_timeframe: Optional[str] = Field(None, description="Expected timeframe to target")
    days_to_target: Optional[int] = Field(None, ge=1, le=30, description="Expected days to target")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="Analysis timestamp")
    expiry_date: datetime = Field(..., description="Signal expiry date")
    
    # Components
    components: Dict[str, SignalComponent] = Field(default_factory=dict, description="Signal components")
    
    # Additional fields for compatibility
    average_weekly_range_pips: Optional[float] = Field(None, description="Average weekly range in pips")
    signal_category: Optional[str] = Field(None, description="Legacy signal category")
    
    # Realistic price fields based on market volatility
    realistic_high: Optional[float] = Field(None, gt=0, description="Realistic high price based on volatility")
    realistic_low: Optional[float] = Field(None, gt=0, description="Realistic low price based on volatility")
    realistic_average: Optional[float] = Field(None, gt=0, description="Realistic average price")
    daily_volatility_factor: Optional[float] = Field(None, description="Daily volatility factor used")
    
    @field_validator('pair')
    @classmethod
    def validate_pair_format(cls, v: str) -> str:
        """Validate currency pair format"""
        import re
        if not re.match(r'^[A-Z]{6}$', v):
            raise ValueError("Currency pair must be 6 uppercase letters (e.g., EURUSD)")
        return v.upper()
    
    @field_validator('expiry_date')
    @classmethod  
    def validate_expiry_date(cls, v: datetime) -> datetime:
        """Validate expiry date is in the future"""
        if v <= datetime.now():
            raise ValueError("Expiry date must be in the future")
        return v
    
    @property
    def high_price(self) -> Optional[float]:
        """Get high price - use realistic high if available, otherwise fallback to old logic"""
        if self.realistic_high:
            return self.realistic_high
        
        # Fallback to old logic if realistic prices not available
        if self.action == SignalAction.BUY and self.exit_price and self.entry_price:
            return max(self.exit_price, self.entry_price)
        elif self.action == SignalAction.SELL and self.entry_price:
            return self.entry_price
        return None
    
    @property
    def low_price(self) -> Optional[float]:
        """Get low price - use realistic low if available, otherwise fallback to old logic"""
        if self.realistic_low:
            return self.realistic_low
            
        # Fallback to old logic if realistic prices not available
        if self.action == SignalAction.BUY and self.entry_price:
            return self.entry_price
        elif self.action == SignalAction.SELL and self.exit_price and self.entry_price:
            return min(self.exit_price, self.entry_price)
        return None
    
    @property
    def mt4_action(self) -> str:
        """Get MT4-compatible action string"""
        return f"MT4 {self.action.value}"


class SignalResult(BaseModel):
    """Complete result from signal generation process"""
    has_real_data: bool = Field(..., description="Whether result contains real market data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Generation timestamp")
    source: str = Field(default="Forex Signal Generation System", description="Data source")
    
    # Signal data
    forex_alerts: List[TradingSignal] = Field(default_factory=list, description="Generated forex signals")
    total_signals: int = Field(default=0, description="Total signals analyzed")
    active_signals: int = Field(default=0, description="Active (non-HOLD) signals")
    hold_signals: int = Field(default=0, description="HOLD signals")
    
    # Analysis metadata
    currency_pairs_analyzed: List[str] = Field(default_factory=list, description="Currency pairs analyzed")
    analysis_weights: Dict[str, float] = Field(default_factory=dict, description="Analysis component weights")
    average_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Average confidence across signals")
    
    # Legacy compatibility fields
    options_alerts: List[Dict[str, Any]] = Field(default_factory=list, description="Options alerts (legacy)")
    swing_trades: List[Dict[str, Any]] = Field(default_factory=list, description="Swing trades (legacy)")
    day_trades: List[Dict[str, Any]] = Field(default_factory=list, description="Day trades (legacy)")
    text_report: Optional[str] = Field(None, description="Formatted text report")
    
    # Error information
    error: Optional[str] = Field(None, description="Error message if generation failed")
    
    def __post_init__(self):
        """Calculate derived fields after initialization"""
        self.total_signals = len(self.forex_alerts)
        self.active_signals = len([s for s in self.forex_alerts if s.action != SignalAction.HOLD])
        self.hold_signals = self.total_signals - self.active_signals
        
        if self.forex_alerts:
            confidences = [s.confidence for s in self.forex_alerts]
            self.average_confidence = sum(confidences) / len(confidences)
            self.currency_pairs_analyzed = [s.pair for s in self.forex_alerts]
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PriceData(BaseModel):
    """Price data from external APIs"""
    pair: str = Field(..., description="Currency pair")
    price: float = Field(..., gt=0, description="Current price")
    bid: Optional[float] = Field(None, gt=0, description="Bid price")
    ask: Optional[float] = Field(None, gt=0, description="Ask price") 
    timestamp: datetime = Field(default_factory=datetime.now, description="Price timestamp")
    source: str = Field(..., description="Data source")
    
    @field_validator('pair')
    @classmethod
    def validate_pair(cls, v: str) -> str:
        """Validate currency pair format"""
        import re
        if not re.match(r'^[A-Z]{6}$', v):
            raise ValueError("Currency pair must be 6 uppercase letters")
        return v.upper()


class ValidationResult(BaseModel):
    """Result of data validation"""
    is_valid: bool = Field(..., description="Whether data passed validation")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    validated_data: Optional[Dict[str, Any]] = Field(None, description="Cleaned/validated data")
    
    @property
    def has_errors(self) -> bool:
        """Check if validation has errors"""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if validation has warnings"""
        return len(self.warnings) > 0