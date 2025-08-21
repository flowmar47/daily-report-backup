"""
Data models for API responses and market data
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator


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


class EconomicData(BaseModel):
    """Economic indicator data"""
    indicator: str = Field(..., description="Economic indicator name")
    country: str = Field(..., description="Country code")
    value: float = Field(..., description="Indicator value")
    previous_value: Optional[float] = Field(None, description="Previous value")
    forecast: Optional[float] = Field(None, description="Forecasted value")
    impact: str = Field(..., description="Impact level (low, medium, high)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Data timestamp")
    source: str = Field(..., description="Data source")


class MarketData(BaseModel):
    """Comprehensive market data"""
    pair: str = Field(..., description="Currency pair")
    prices: List[PriceData] = Field(default_factory=list, description="Price data from multiple sources")
    economic_indicators: List[EconomicData] = Field(default_factory=list, description="Economic indicators")
    technical_data: Dict[str, Any] = Field(default_factory=dict, description="Technical analysis data")
    sentiment_data: Dict[str, Any] = Field(default_factory=dict, description="Sentiment analysis data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Data collection timestamp")
    
    @property
    def average_price(self) -> Optional[float]:
        """Calculate average price from all sources"""
        if not self.prices:
            return None
        return sum(p.price for p in self.prices) / len(self.prices)
    
    @property
    def price_consensus(self) -> bool:
        """Check if prices from different sources are in consensus"""
        if len(self.prices) < 2:
            return True
        
        avg_price = self.average_price
        if avg_price is None:
            return False
        
        # Check if all prices are within 0.1% of average
        tolerance = avg_price * 0.001
        return all(abs(p.price - avg_price) <= tolerance for p in self.prices)


class APIResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool = Field(..., description="Whether the API call was successful")
    data: Dict[str, Any] = Field(default_factory=dict, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")
    source: str = Field(..., description="API source")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    rate_limit_remaining: Optional[int] = Field(None, description="Remaining API calls")
    rate_limit_reset: Optional[datetime] = Field(None, description="Rate limit reset time")