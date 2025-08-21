"""
Utility functions for daily financial report automation
Enhanced with comprehensive error handling and validation
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Import error handling
try:
    from error_handler import resilient_operation, ErrorSeverity
except ImportError:
    # Fallback decorator if error_handler not available
    def resilient_operation(context: str, severity: str = "MEDIUM", 
                           max_retries: int = 3, fallback_result = None):
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Error in {context}: {e}")
                    return fallback_result
            return wrapper
        return decorator
    
    class ErrorSeverity:
        CRITICAL = "CRITICAL"
        HIGH = "HIGH"
        MEDIUM = "MEDIUM"
        LOW = "LOW"

class ForexParser:
    """Parse forex data from scraped content"""
    
    CURRENCY_PAIRS = [
        'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'EURGBP', 'GBPCAD',
        'CHFJPY', 'NZDJPY', 'AUDUSD', 'AUDJPY', 'CADJPY', 'USDCAD',
        'EURJPY', 'GBPJPY', 'NZDUSD', 'EURCHF', 'GBPCHF', 'AUDCAD'
    ]
    
    SIGNAL_KEYWORDS = {
        'buy': ['buy', 'long', 'bullish', 'uptrend', 'support'],
        'sell': ['sell', 'short', 'bearish', 'downtrend', 'resistance'],
        'neutral': ['neutral', 'range', 'consolidation', 'sideways']
    }
    
    @classmethod
    @resilient_operation("forex_signal_extraction", ErrorSeverity.HIGH, fallback_result={})
    def extract_forex_signals(cls, raw_text: str, tables: List = None) -> Dict:
        """Extract forex signals from raw scraped data with enhanced validation"""
        signals = {}
        
        if not raw_text and not tables:
            logger.warning("No input data provided for forex signal extraction")
            return signals
        
        # Process text content
        if raw_text:
            try:
                lines = raw_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    for pair in cls.CURRENCY_PAIRS:
                        if pair in line.upper():
                            signal = cls._determine_signal(line)
                            price = cls._extract_price(line)
                            
                            if signal and price:
                                # Validate price format
                                if cls._validate_price(price, pair):
                                    signals[pair] = {
                                        'signal': signal,
                                        'price': price,
                                        'raw_text': line.strip(),
                                        'confidence': cls._calculate_confidence(line),
                                        'extracted_at': datetime.now().isoformat()
                                    }
                                else:
                                    logger.warning(f"Invalid price format for {pair}: {price}")
            except Exception as e:
                logger.error(f"Error processing text content: {e}")
        
        # Process tables
        if tables:
            try:
                for table in tables:
                    table_signals = cls._parse_table_signals(table)
                    # Merge without overwriting higher quality data
                    for pair, data in table_signals.items():
                        if pair not in signals or data.get('confidence', 0) > signals[pair].get('confidence', 0):
                            signals[pair] = data
            except Exception as e:
                logger.error(f"Error processing table data: {e}")
        
        logger.info(f"Extracted {len(signals)} forex signals")
        return signals
    
    @classmethod
    def _determine_signal(cls, text: str) -> Optional[str]:
        """Determine signal type from text"""
        text_lower = text.lower()
        
        for signal_type, keywords in cls.SIGNAL_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                return signal_type.upper()
        
        return None
    
    @classmethod
    def _extract_price(cls, text: str) -> Optional[str]:
        """Extract price from text"""
        # Look for price patterns
        price_patterns = [
            r'\b\d+\.\d{2,5}\b',  # Standard forex price
            r'\b\d{1,3}\.\d{2,4}\b',  # JPY pairs
            r'@\s*(\d+\.?\d*)',  # Price after @
            r':\s*(\d+\.?\d*)',  # Price after :
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0).replace('@', '').replace(':', '').strip()
        
        return None
    
    @classmethod
    def _parse_table_signals(cls, table: List[List[str]]) -> Dict:
        """Parse signals from table data"""
        signals = {}
        
        if not table:
            return signals
        
        # Try to identify headers
        headers = [h.lower() for h in table[0]] if table else []
        
        # Look for relevant columns
        pair_col = None
        signal_col = None
        price_col = None
        
        for i, header in enumerate(headers):
            if any(term in header for term in ['pair', 'symbol', 'currency']):
                pair_col = i
            elif any(term in header for term in ['signal', 'action', 'recommendation']):
                signal_col = i
            elif any(term in header for term in ['price', 'entry', 'rate']):
                price_col = i
        
        # Extract data from rows
        for row in table[1:]:
            if pair_col is not None and pair_col < len(row):
                pair = row[pair_col].upper().replace(' ', '').replace('/', '')
                if pair in cls.CURRENCY_PAIRS:
                    signal_data = {'pair': pair}
                    
                    if signal_col is not None and signal_col < len(row):
                        signal_data['signal'] = cls._determine_signal(row[signal_col])
                    
                    if price_col is not None and price_col < len(row):
                        signal_data['price'] = cls._extract_price(row[price_col])
                    
                    if signal_data.get('signal'):
                        signals[pair] = signal_data
        
        return signals
    
    @classmethod
    def _validate_price(cls, price: str, pair: str) -> bool:
        """Validate price format for currency pair"""
        try:
            price_float = float(price.replace(',', ''))
            
            # Basic range validation
            if 'JPY' in pair:
                return 50 <= price_float <= 200  # JPY pairs typically in this range
            else:
                return 0.1 <= price_float <= 10   # Most other pairs
                
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def _calculate_confidence(cls, text: str) -> float:
        """Calculate confidence score for signal extraction"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for explicit signals
        if any(keyword in text.lower() for keyword in ['strong', 'confirmed', 'breakout']):
            confidence += 0.2
        
        # Increase confidence for price targets
        if any(keyword in text.lower() for keyword in ['target', 'tp', 'take profit']):
            confidence += 0.1
        
        # Increase confidence for stop loss levels
        if any(keyword in text.lower() for keyword in ['stop', 'sl', 'stop loss']):
            confidence += 0.1
        
        return min(confidence, 1.0)


class ReportFormatter:
    """Format report for different outputs"""
    
    @classmethod
    def format_for_telegram(cls, report_data: Dict, template_path: str = 'example.md') -> str:
        """Format report data for Telegram using markdown template"""
        try:
            # Read template
            with open(template_path, 'r') as f:
                template = f.read()
            
            # Replace placeholders
            report = template
            report = report.replace('[DATE]', datetime.now().strftime('%Y-%m-%d'))
            report = report.replace('[TIME]', datetime.now().strftime('%H:%M:%S'))
            
            # Format forex section
            forex_section = cls._format_forex_section(report_data.get('forex_data', {}))
            report = cls._insert_section(report, '### 📈 Today\'s Strongest Signals', forex_section)
            
            # Format options section
            options_section = cls._format_options_section(report_data.get('options_data', []))
            report = cls._insert_section(report, '## 📈 Options Trading Opportunities', options_section)
            
            # Format risk warnings
            risk_section = cls._format_risk_section(report_data)
            report = cls._insert_section(report, '## ⚠️ Risk Warnings', risk_section)
            
            return report
            
        except Exception as e:
            logger.error(f"Error formatting report: {str(e)}")
            return cls._fallback_format(report_data)
    
    @classmethod
    def _format_forex_section(cls, forex_data: Dict) -> str:
        """Format forex data section"""
        if not forex_data:
            return "No forex signals available today."
        
        buy_signals = []
        sell_signals = []
        
        for pair, data in forex_data.items():
            if isinstance(data, dict) and data.get('signal'):
                row = f"| {pair} | {data.get('price', 'N/A')} | - | - | {data.get('signal_strength', 'MODERATE')} |"
                
                if data['signal'] == 'BUY':
                    buy_signals.append(row)
                elif data['signal'] == 'SELL':
                    sell_signals.append(row)
        
        section = ""
        if buy_signals:
            section += "#### 🟢 **BUY SIGNALS**\n"
            section += "| Pair | Entry | Stop Loss | Take Profit | Signal Strength |\n"
            section += "|------|-------|-----------|-------------|-----------------|​\n"
            section += '\n'.join(buy_signals) + '\n\n'
        
        if sell_signals:
            section += "#### 🔴 **SELL SIGNALS**\n"
            section += "| Pair | Entry | Stop Loss | Take Profit | Signal Strength |\n"
            section += "|------|-------|-----------|-------------|-----------------|​\n"
            section += '\n'.join(sell_signals) + '\n'
        
        return section
    
    @classmethod
    def _format_options_section(cls, options_data: List) -> str:
        """Format options section from MyMama data"""
        if not options_data:
            return "No options data available today."
        
        section = ""
        for option in options_data:
            ticker = option.get('ticker', 'N/A')
            high_52w = option.get('high_52week', 'N/A')
            low_52w = option.get('low_52week', 'N/A')
            call_strike = option.get('call_strike', 'N/A')
            put_strike = option.get('put_strike', 'N/A')
            status = option.get('status', 'N/A')
            
            section += f"\n### 🎯 {ticker}\n"
            section += f"**52W High:** {high_52w} | **Low:** {low_52w}\n"
            if call_strike != 'N/A':
                section += f"**CALL:** > {call_strike}\n"
            if put_strike != 'N/A':
                section += f"**PUT:** < {put_strike}\n"
            section += f"**Status:** {status}\n\n"
        
        return section
    
    @classmethod
    def _format_risk_section(cls, report_data: Dict) -> str:
        """Format risk warnings section"""
        section = "\n### 🔗 Forex-Options Correlations\n"
        
        correlations = report_data.get('correlations', {}).get('forex_options', [])
        if correlations:
            for corr in correlations:
                section += f"- {corr}\n"
        else:
            section += "- Monitor for potential correlations between forex and options positions\n"
        
        section += "\n### 📅 Today's Key Events\n"
        section += "- Check economic calendar for updates\n"
        section += "- Monitor earnings announcements\n"
        
        return section
    
    @classmethod
    def _insert_section(cls, template: str, section_marker: str, content: str) -> str:
        """Insert content after section marker"""
        lines = template.split('\n')
        new_lines = []
        inserted = False
        
        for i, line in enumerate(lines):
            new_lines.append(line)
            if section_marker in line and not inserted:
                # Skip existing content until next section
                j = i + 1
                while j < len(lines) and not lines[j].startswith('#'):
                    j += 1
                new_lines.append(content)
                inserted = True
                # Skip the old content
                return '\n'.join(new_lines[:i+1] + [content] + lines[j:])
        
        return template
    
    @classmethod
    def _fallback_format(cls, report_data: Dict) -> str:
        """Simple fallback format if template fails"""
        return f"""📊 Daily Financial Report - {datetime.now().strftime('%Y-%m-%d')}

💱 Forex Signals:
{json.dumps(report_data.get('forex_data', {}), indent=2)}

📈 Options Plays:
{json.dumps(report_data.get('options_data', {}), indent=2)}

⚠️ Generated by automated system"""


class ValidationHelper:
    """Validate data quality and completeness"""
    
    @classmethod
    def validate_forex_data(cls, forex_data: Dict) -> Tuple[bool, List[str]]:
        """Validate forex data completeness"""
        issues = []
        
        if not forex_data:
            issues.append("No forex data collected")
            return False, issues
        
        valid_pairs = 0
        for pair, data in forex_data.items():
            if isinstance(data, dict):
                if not data.get('signal'):
                    issues.append(f"{pair}: Missing signal")
                if not data.get('price'):
                    issues.append(f"{pair}: Missing price")
                else:
                    valid_pairs += 1
        
        if valid_pairs < 3:
            issues.append(f"Only {valid_pairs} valid forex pairs found")
        
        return len(issues) == 0, issues
    
