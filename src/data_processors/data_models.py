"""
Data models for structured financial alerts formatting.
Implements the exact output format specified in requirements.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class ForexForecast:
    """Forex forecast data model matching specified format."""
    pair: str
    high: str
    average: str
    low: str
    fourteen_day_average: str
    trade_type: str  # e.g., "MT4 BUY < 81.99" or "MT4 SELL < 0.6390"
    exit: str
    trade_status: Optional[str] = None  # e.g., "TRADE IN PROFIT"
    special_badge: Optional[str] = None  # e.g., "NEW!"
    chart_image_url: Optional[str] = None

    def format_output(self) -> str:
        """Format forex forecast according to specification."""
        output = f"""Pair: {self.pair}
High: {self.high}
Average: {self.average}
Low: {self.low}
MT4 Action: {self.trade_type}
Exit: {self.exit}"""

        # Add notes on same line if available
        notes = []
        if self.trade_status:
            notes.append(self.trade_status)
        if self.special_badge:
            notes.append(self.special_badge)
        
        if notes:
            output += f"\nNotes: {', '.join(notes)}"
        
        if self.chart_image_url:
            output += f"\nChart/Image URL: {self.chart_image_url}"
        
        return output


@dataclass
class StockCryptoForecast:
    """Stock & Crypto forecast data model."""
    ticker: str
    direction: str
    entry: str
    take_profit: str
    stop_loss: str
    status: str
    chart_image_url: Optional[str] = None

    def format_output(self) -> str:
        """Format stock/crypto forecast according to specification."""
        output = f"""Ticker: {self.ticker}
Direction: {self.direction}
Entry: {self.entry}
Take Profit: {self.take_profit}
Stop Loss: {self.stop_loss}
Status: {self.status}"""

        if self.chart_image_url:
            output += f"\nChart/Image URL: {self.chart_image_url}"
        
        return output


@dataclass
class OptionsTrade:
    """Options trade data model matching specified format."""
    ticker: str
    fifty_two_week_high: str
    fifty_two_week_low: str
    call_strike: str  # e.g., "CALL > 352.42"
    put_strike: str   # e.g., "PUT < 345.45"
    trade_status: Optional[str] = None  # e.g., "trade in profit"
    special_badge: Optional[str] = None  # e.g., "NEW!"
    asset_image_url: Optional[str] = None

    def format_output(self) -> str:
        """Format options trade according to specification."""
        output = f"""Symbol: {self.ticker}
52 Week High: {self.fifty_two_week_high}
52 Week Low: {self.fifty_two_week_low}
Strike Price:

{self.call_strike}

{self.put_strike}
Status: {self.trade_status if self.trade_status else 'ACTIVE'}"""

        if self.special_badge:
            output += f"\nSpecial Badge: {self.special_badge}"
        
        if self.asset_image_url:
            output += f"\nChart/Image URL: {self.asset_image_url}"
        
        return output


@dataclass
class SwingTrade:
    """Premium swing trade data model."""
    company: str
    ticker: str
    earnings_date: str
    current_price: str
    rationale: str

    def format_output(self) -> str:
        """Format swing trade according to specification."""
        return f"""{self.company} ({self.ticker})
Earnings Report: {self.earnings_date}
Current Price: {self.current_price}
Rationale: {self.rationale}"""


@dataclass
class DayTrade:
    """Premium day trade data model."""
    company: str
    ticker: str
    earnings_date: str
    current_price: str
    rationale: str

    def format_output(self) -> str:
        """Format day trade according to specification."""
        return f"""{self.company} ({self.ticker})
Earnings Report: {self.earnings_date}
Current Price: {self.current_price}
Rationale: {self.rationale}"""


@dataclass
class EarningsReport:
    """Earnings report data model."""
    company: str
    ticker: str
    earnings_date: str
    current_price: str
    rationale: str

    def format_output(self) -> str:
        """Format earnings report according to specification."""
        return f"""Company: {self.company} ({self.ticker})
Earnings Report: {self.earnings_date}
Current Price: {self.current_price}
Rationale: {self.rationale}"""


@dataclass
class TableSection:
    """Table section data model."""
    title: str
    headers: List[str]
    rows: List[List[str]]

    def format_output(self) -> str:
        """Format table section according to specification."""
        output = f"Table Title: {self.title}\n\n"
        output += f"Headers: {', '.join(self.headers)}\n\n"
        output += "Rows:\n\n"
        
        for row in self.rows:
            output += f"{', '.join(row)}\n\n"
        
        return output.rstrip()


@dataclass
class StructuredFinancialReport:
    """Complete structured financial report."""
    forex_forecasts: List[ForexForecast] = field(default_factory=list)
    stock_crypto_forecasts: List[StockCryptoForecast] = field(default_factory=list)
    options_trades: List[OptionsTrade] = field(default_factory=list)
    swing_trades: List[SwingTrade] = field(default_factory=list)
    day_trades: List[DayTrade] = field(default_factory=list)
    earnings_reports: List[EarningsReport] = field(default_factory=list)
    table_sections: List[TableSection] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    source_url: Optional[str] = None
    scraper_version: str = "2.0"

    def format_complete_report(self) -> str:
        """Format the complete report with all sections using exact template format."""
        sections = []
        
        # Forex Forecasts Section
        if self.forex_forecasts:
            sections.append("FOREX PAIRS")
            sections.append("")
            for i, forecast in enumerate(self.forex_forecasts):
                sections.append(forecast.format_output())
                if i < len(self.forex_forecasts) - 1:
                    sections.append("")
        
        # Stocks & Crypto Forecasts Section
        if self.stock_crypto_forecasts:
            if sections:  # Add spacing if other sections exist
                sections.append("")
            sections.append("Stocks & Crypto Forecasts")
            sections.append("")
            for i, forecast in enumerate(self.stock_crypto_forecasts):
                sections.append(forecast.format_output())
                if i < len(self.stock_crypto_forecasts) - 1:
                    sections.append("")
        
        # Options Trades Section
        if self.options_trades:
            if sections:
                sections.append("")
            sections.append("EQUITIES AND OPTIONS")
            sections.append("")
            for i, trade in enumerate(self.options_trades):
                sections.append(trade.format_output())
                if i < len(self.options_trades) - 1:
                    sections.append("")
        
        # Premium Swing Trades Section
        if self.swing_trades:
            if sections:
                sections.append("")
            sections.append("PREMIUM SWING TRADES (Monday - Wednesday)")
            sections.append("")
            for i, trade in enumerate(self.swing_trades):
                sections.append(trade.format_output())
                if i < len(self.swing_trades) - 1:
                    sections.append("")
        
        # Premium Day Trades Section
        if self.day_trades:
            if sections:
                sections.append("")
            sections.append("PREMIUM DAY TRADES (Monday - Wednesday)")
            sections.append("")
            for i, trade in enumerate(self.day_trades):
                sections.append(trade.format_output())
                if i < len(self.day_trades) - 1:
                    sections.append("")
        
        # Earnings Reports Section
        if self.earnings_reports:
            if sections:
                sections.append("")
            sections.append("Earnings Reports")
            sections.append("")
            for i, report in enumerate(self.earnings_reports):
                sections.append(report.format_output())
                if i < len(self.earnings_reports) - 1:
                    sections.append("")
        
        # Table Section
        if self.table_sections:
            if sections:
                sections.append("")
            sections.append("Table Section")
            sections.append("")
            for i, table in enumerate(self.table_sections):
                sections.append(table.format_output())
                if i < len(self.table_sections) - 1:
                    sections.append("")
        
        return "\n".join(sections)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'forex_forecasts': [
                {
                    'pair': f.pair,
                    'high': f.high,
                    'average': f.average,
                    'low': f.low,
                    'fourteen_day_average': f.fourteen_day_average,
                    'trade_type': f.trade_type,
                    'exit': f.exit,
                    'trade_status': f.trade_status,
                    'special_badge': f.special_badge,
                    'chart_image_url': f.chart_image_url
                } for f in self.forex_forecasts
            ],
            'stock_crypto_forecasts': [
                {
                    'ticker': f.ticker,
                    'direction': f.direction,
                    'entry': f.entry,
                    'take_profit': f.take_profit,
                    'stop_loss': f.stop_loss,
                    'status': f.status,
                    'chart_image_url': f.chart_image_url
                } for f in self.stock_crypto_forecasts
            ],
            'options_trades': [
                {
                    'ticker': o.ticker,
                    'fifty_two_week_high': o.fifty_two_week_high,
                    'fifty_two_week_low': o.fifty_two_week_low,
                    'call_strike': o.call_strike,
                    'put_strike': o.put_strike,
                    'trade_status': o.trade_status,
                    'special_badge': o.special_badge,
                    'asset_image_url': o.asset_image_url
                } for o in self.options_trades
            ],
            'swing_trades': [
                {
                    'company': s.company,
                    'ticker': s.ticker,
                    'earnings_date': s.earnings_date,
                    'current_price': s.current_price,
                    'rationale': s.rationale
                } for s in self.swing_trades
            ],
            'day_trades': [
                {
                    'company': d.company,
                    'ticker': d.ticker,
                    'earnings_date': d.earnings_date,
                    'current_price': d.current_price,
                    'rationale': d.rationale
                } for d in self.day_trades
            ],
            'earnings_reports': [
                {
                    'company': e.company,
                    'ticker': e.ticker,
                    'earnings_date': e.earnings_date,
                    'current_price': e.current_price,
                    'rationale': e.rationale
                } for e in self.earnings_reports
            ],
            'table_sections': [
                {
                    'title': t.title,
                    'headers': t.headers,
                    'rows': t.rows
                } for t in self.table_sections
            ],
            'metadata': {
                'timestamp': self.timestamp.isoformat(),
                'source_url': self.source_url,
                'scraper_version': self.scraper_version
            }
        }

    def get_summary_stats(self) -> Dict[str, int]:
        """Get summary statistics of the report."""
        return {
            'forex_forecasts': len(self.forex_forecasts),
            'stock_crypto_forecasts': len(self.stock_crypto_forecasts),
            'options_trades': len(self.options_trades),
            'swing_trades': len(self.swing_trades),
            'day_trades': len(self.day_trades),
            'earnings_reports': len(self.earnings_reports),
            'table_sections': len(self.table_sections),
            'total_entries': (
                len(self.forex_forecasts) + 
                len(self.stock_crypto_forecasts) + 
                len(self.options_trades) + 
                len(self.swing_trades) + 
                len(self.day_trades) + 
                len(self.earnings_reports) + 
                len(self.table_sections)
            )
        }