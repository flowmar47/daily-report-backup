"""
Template generator for structured financial alerts messages.
Implements the exact format specification for Signal and Telegram delivery.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class StructuredTemplateGenerator:
    """Generates structured financial alerts messages using exact template format."""
    
    def __init__(self):
        """Initialize the template generator."""
        pass
    
    def generate_structured_message(self, financial_data: Dict[str, Any]) -> str:
        """
        Generate structured message using exact template format.
        Only includes sections that have actual data - no placeholders or N/A sections.
        
        Args:
            financial_data: Dictionary containing forex_alerts, options_data, 
                          swing_trades, day_trades, earnings_releases
                          
        Returns:
            Formatted message string following exact template specification
        """
        if not financial_data or not financial_data.get('has_real_data'):
            return "No financial signals available today."
        
        sections = []
        
        # FOREX PAIRS Section - only if forex data exists
        forex_alerts = financial_data.get('forex_alerts', {})
        if forex_alerts:
            # Convert dict to list format if needed
            if isinstance(forex_alerts, dict):
                forex_list = []
                for pair, data in forex_alerts.items():
                    alert = data.copy() if isinstance(data, dict) else {}
                    alert['pair'] = pair
                    forex_list.append(alert)
                forex_section = self._format_forex_section(forex_list)
            else:
                forex_section = self._format_forex_section(forex_alerts)
            if forex_section:
                sections.append(forex_section)
        
        # PREMIUM SWING TRADES Section - only if swing trades exist
        swing_trades = financial_data.get('swing_trades', [])
        if swing_trades:
            swing_section = self._format_swing_trades_section(swing_trades)
            if swing_section:
                sections.append(swing_section)
        
        # PREMIUM DAY TRADES Section - only if day trades exist
        day_trades = financial_data.get('day_trades', [])
        if day_trades:
            day_section = self._format_day_trades_section(day_trades)
            if day_section:
                sections.append(day_section)
        
        # EQUITIES AND OPTIONS Section - only if options data exists  
        options_data = financial_data.get('options_data', [])
        if options_data:
            options_section = self._format_options_section(options_data)
            if options_section:
                sections.append(options_section)
        
        # Join sections with double line breaks
        message = "\n\n".join(sections)
        
        if not message.strip():
            return "No financial signals available today."
        
        return message
    
    def _format_forex_section(self, forex_alerts: list) -> str:
        """Format FOREX PAIRS section according to template."""
        if not forex_alerts:
            return ""
        
        section_lines = ["FOREX PAIRS", ""]
        
        # Filter out invalid pairs (corrupted data from scraping)
        valid_pairs = []
        for alert in forex_alerts:
            pair = alert.get('pair', '')
            # Skip corrupted pairs like "ALERTS", "AVERAG", "PROFIT", "TRADIN"
            if pair and len(pair) >= 6 and '/' in pair or pair.upper() in ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD', 'EURGBP', 'EURJPY', 'GBPJPY']:
                valid_pairs.append(alert)
        
        if not valid_pairs:
            return "FOREX PAIRS\n\nNo valid forex signals available today."
        
        for alert in valid_pairs:
            pair = alert.get('pair', 'N/A')
            pair_lines = [f"Pair: {pair}"]
            
            # Extract values with fallback to template placeholders
            high = alert.get('high', 'N/A')
            average = alert.get('average', 'N/A') 
            low = alert.get('low', 'N/A')
            mt4_action = alert.get('signal', alert.get('trade_type', 'N/A'))
            exit_price = alert.get('exit_price', alert.get('exit', 'N/A'))
            
            # Format MT4 Action properly
            if mt4_action and mt4_action != 'N/A':
                if 'MT4' not in mt4_action.upper():
                    mt4_action = f"MT4 {mt4_action}"
            
            pair_lines.extend([
                f"High: {high}",
                f"Average: {average}",
                f"Low: {low}",
                f"MT4 Action: {mt4_action}",
                f"Exit: {exit_price}"
            ])
            
            # Add notes if available
            notes = []
            if alert.get('trade_status'):
                notes.append(alert['trade_status'])
            if alert.get('special_badge'):
                notes.append(alert['special_badge'])
            
            if notes:
                pair_lines.append(f"Notes: {', '.join(notes)}")
            
            section_lines.extend(pair_lines)
            section_lines.append("")  # Empty line between pairs
        
        # Remove trailing empty line
        if section_lines and section_lines[-1] == "":
            section_lines.pop()
        
        return "\n".join(section_lines)
    
    def _format_swing_trades_section(self, swing_trades: List[Dict[str, Any]]) -> str:
        """Format PREMIUM SWING TRADES section according to template."""
        if not swing_trades:
            return ""
        
        section_lines = ["PREMIUM SWING TRADES", "", "Monday - Wednesday"]
        
        for trade in swing_trades:
            company = trade.get('company', 'N/A')
            ticker = trade.get('ticker', 'N/A')
            earnings_date = trade.get('earnings_date', 'N/A')
            analysis = self._clean_unicode_text(trade.get('analysis', 'N/A'))
            strategy = self._clean_unicode_text(trade.get('strategy', 'N/A'))
            
            # Format company name with ticker
            if ticker != 'N/A':
                company_line = f"{ticker} - {company}"
            else:
                company_line = company
            
            trade_lines = ["", company_line, ""]
            
            if earnings_date != 'N/A':
                trade_lines.append(f"    EARNINGS DATE: {earnings_date}")
            if analysis != 'N/A':
                trade_lines.append(f"    ANALYSIS: {analysis}")
            if strategy != 'N/A':
                trade_lines.append(f"    STRATEGY: {strategy}")
            
            section_lines.extend(trade_lines)
        
        return "\n".join(section_lines)
    
    def _format_day_trades_section(self, day_trades: List[Dict[str, Any]]) -> str:
        """Format PREMIUM DAY TRADES section according to template."""
        if not day_trades:
            return ""
        
        section_lines = ["PREMIUM DAY TRADES", "", "Monday - Wednesday"]
        
        for trade in day_trades:
            company = trade.get('company', 'N/A')
            ticker = trade.get('ticker', 'N/A')
            why_day_trade = self._clean_unicode_text(trade.get('why_day_trade', 'N/A'))
            
            # Format company name with ticker
            if ticker != 'N/A':
                company_line = f"{ticker} - {company}"
            else:
                company_line = company
            
            trade_lines = ["", company_line, ""]
            
            if why_day_trade != 'N/A':
                trade_lines.append(f"    WHY DAY TRADE: {why_day_trade}")
            
            section_lines.extend(trade_lines)
        
        return "\n".join(section_lines)
    
    def _format_options_section(self, options_data: List[Dict[str, Any]]) -> str:
        """Format EQUITIES AND OPTIONS section according to template."""
        if not options_data:
            return ""
        
        section_lines = ["EQUITIES AND OPTIONS", ""]
        
        for option in options_data:
            symbol = option.get('ticker', option.get('symbol', 'N/A'))
            high_52w = option.get('high_52week', option.get('week_high', 'N/A'))
            low_52w = option.get('low_52week', option.get('week_low', 'N/A'))
            call_strike = option.get('call_strike', 'N/A')
            put_strike = option.get('put_strike', 'N/A')
            status = option.get('status', 'N/A')
            
            # Skip entries with no symbol or only "EXIT"
            if not symbol or symbol == 'N/A' or symbol == 'EXIT':
                continue
            
            # Extract numeric values from strike price strings
            call_value = self._extract_strike_value(call_strike)
            put_value = self._extract_strike_value(put_strike)
            
            option_lines = [
                f"Symbol: {symbol}",
                f"52 Week High: {high_52w}",
                f"52 Week Low: {low_52w}",
                "Strike Price:",
                "",
                f"CALL > {call_value}",
                "",
                f"PUT < {put_value}",
                f"Status: {status}",
                ""  # Empty line between options
            ]
            
            section_lines.extend(option_lines)
        
        # Remove trailing empty line
        if section_lines and section_lines[-1] == "":
            section_lines.pop()
        
        return "\n".join(section_lines)
    
    def _extract_strike_value(self, strike_string: str) -> str:
        """Extract numeric value from strike price string."""
        if not strike_string or strike_string == 'N/A':
            return 'N/A'
        
        # If it already starts with CALL > or PUT <, extract just the value part after the operator
        if strike_string.startswith('CALL >'):
            return strike_string.replace('CALL >', '').strip()
        elif strike_string.startswith('PUT <'):
            return strike_string.replace('PUT <', '').strip()
        
        # Extract number from strings like "352.42"
        import re
        match = re.search(r'([\d.]+)', strike_string)
        if match:
            return match.group(1)
        
        return strike_string
    
    def _clean_unicode_text(self, text: str) -> str:
        """Clean unicode characters and unwanted text from scraped content."""
        if not text or text == 'N/A':
            return 'N/A'
        
        # Remove zero-width space and other problematic unicode characters
        text = text.replace('\u200b', '')  # Zero-width space
        text = text.replace('\u200c', '')  # Zero-width non-joiner
        text = text.replace('\u200d', '')  # Zero-width joiner
        text = text.replace('\u2013', '-')  # En dash to regular dash
        text = text.replace('\u2014', '--') # Em dash to double dash
        
        # Clean up day trade specific content
        if 'FORECAST' in text:
            text = text.split('FORECAST')[0].strip()
        if 'ALERTS' in text:
            text = text.split('ALERTS')[0].strip()
        if 'PREMIUM' in text:
            text = text.split('PREMIUM')[0].strip()
        if 'OPTIONS' in text:
            text = text.split('OPTIONS')[0].strip()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def generate_earnings_section(self, earnings_data: List[Dict[str, Any]]) -> str:
        """
        Generate earnings section if needed as a separate section.
        This can be integrated into swing/day trades or kept separate.
        """
        if not earnings_data:
            return ""
        
        section_lines = ["MOST ANTICIPATED EARNINGS RELEASES", ""]
        
        for earning in earnings_data:
            company = earning.get('company', 'N/A')
            ticker = earning.get('ticker', 'N/A')
            earnings_date = earning.get('earnings_date', 'N/A')
            current_price = earning.get('current_price', 'N/A')
            rationale = earning.get('rationale', 'N/A')
            
            earning_lines = [
                f"{company} ({ticker})",
                f"Earnings Report: {earnings_date}",
                f"Current Price: {current_price}",
                f"Rationale: {rationale}",
                ""  # Empty line between earnings
            ]
            
            section_lines.extend(earning_lines)
        
        # Remove trailing empty line
        if section_lines and section_lines[-1] == "":
            section_lines.pop()
        
        return "\n".join(section_lines)


def format_message_for_platform(financial_data: Dict[str, Any], platform: str = "signal") -> str:
    """
    Format financial data for specific messaging platform.
    
    Args:
        financial_data: Raw financial data dictionary
        platform: Target platform ("signal" or "telegram")
        
    Returns:
        Formatted message string
    """
    generator = StructuredTemplateGenerator()
    message = generator.generate_structured_message(financial_data)
    
    # Platform-specific formatting adjustments
    if platform.lower() == "telegram":
        # Telegram supports markdown - could add formatting if needed
        # For now, keep plain text format as specified
        pass
    elif platform.lower() == "signal":
        # Signal uses plain text - no additional formatting needed
        pass
    
    # Add timestamp and source info
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    footer = f"\n\nGenerated: {timestamp}\nSource: MyMama Financial Alerts"
    
    return message + footer