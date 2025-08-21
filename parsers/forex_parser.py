"""
Forex signal parser for extracting currency pair trading signals.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from bs4 import BeautifulSoup
from ..data_models import ForexSignal, SignalType

logger = logging.getLogger(__name__)


class ForexParser:
    """Parser for extracting forex trading signals from various formats."""
    
    # Common currency pairs to look for
    MAJOR_PAIRS = [
        'EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CHF', 'AUD/USD', 'USD/CAD', 'NZD/USD',
        'EUR/GBP', 'EUR/JPY', 'GBP/JPY', 'EUR/CHF', 'EUR/AUD', 'EUR/CAD', 'GBP/CHF',
        'GBP/AUD', 'GBP/CAD', 'AUD/JPY', 'CAD/JPY', 'NZD/JPY', 'AUD/NZD', 'EUR/NZD',
        'GBP/NZD', 'CHF/JPY', 'AUD/CHF', 'AUD/CAD', 'CAD/CHF', 'NZD/CHF', 'NZD/CAD',
        'XAU/USD', 'XAG/USD', 'USD/MXN', 'USD/ZAR', 'USD/SGD', 'USD/HKD'
    ]
    
    # Signal keywords mapping
    SIGNAL_KEYWORDS = {
        SignalType.BUY: ['buy', 'long', 'bullish', 'up', 'call', 'above', 'breakout'],
        SignalType.SELL: ['sell', 'short', 'bearish', 'down', 'put', 'below', 'breakdown'],
        SignalType.NEUTRAL: ['neutral', 'wait', 'hold', 'sideways', 'range']
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize forex parser with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.custom_pairs = self.config.get('custom_pairs', [])
        self.all_pairs = self.MAJOR_PAIRS + self.custom_pairs
    
    def parse_html_content(self, html_content: str) -> List[ForexSignal]:
        """
        Parse forex signals from HTML content.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            List of ForexSignal objects
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        signals = []
        
        # Try multiple parsing strategies
        signals.extend(self._parse_table_signals(soup))
        signals.extend(self._parse_text_signals(soup))
        signals.extend(self._parse_structured_divs(soup))
        
        # Remove duplicates
        unique_signals = self._deduplicate_signals(signals)
        
        logger.info(f"Parsed {len(unique_signals)} unique forex signals")
        return unique_signals
    
    def parse_text_content(self, text_content: str) -> List[ForexSignal]:
        """
        Parse forex signals from plain text content.
        
        Args:
            text_content: Plain text content
            
        Returns:
            List of ForexSignal objects
        """
        signals = []
        lines = text_content.split('\n')
        
        for i, line in enumerate(lines):
            # Look for currency pairs
            for pair in self.all_pairs:
                if pair in line.upper():
                    signal = self._extract_signal_from_text(line, pair, lines[max(0, i-2):min(len(lines), i+3)])
                    if signal:
                        signals.append(signal)
        
        return self._deduplicate_signals(signals)
    
    def _parse_table_signals(self, soup: BeautifulSoup) -> List[ForexSignal]:
        """Parse signals from HTML tables."""
        signals = []
        
        for table in soup.find_all('table'):
            headers = []
            
            # Get headers
            header_row = table.find('tr')
            if header_row:
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
            
            # Parse data rows
            for row in table.find_all('tr')[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    signal = self._parse_table_row(cells, headers)
                    if signal:
                        signals.append(signal)
        
        return signals
    
    def _parse_table_row(self, cells: List, headers: List[str]) -> Optional[ForexSignal]:
        """Parse a single table row into a forex signal."""
        try:
            row_data = {}
            
            # Map cells to headers
            for i, cell in enumerate(cells):
                if i < len(headers):
                    row_data[headers[i]] = cell.get_text(strip=True)
            
            # Extract pair
            pair = None
            for key in ['pair', 'currency', 'symbol', 'instrument']:
                if key in row_data:
                    potential_pair = row_data[key].upper()
                    if self._is_valid_pair(potential_pair):
                        pair = potential_pair
                        break
            
            if not pair:
                # Check all cells for pairs
                for cell in cells:
                    text = cell.get_text(strip=True).upper()
                    for p in self.all_pairs:
                        if p in text:
                            pair = p
                            break
                    if pair:
                        break
            
            if not pair:
                return None
            
            # Extract signal
            signal_type = self._extract_signal_type(row_data, cells)
            
            # Extract prices
            entry_price = self._extract_price(row_data, ['entry', 'price', 'open'])
            stop_loss = self._extract_price(row_data, ['stop', 'sl', 'stop loss'])
            take_profit = self._extract_price(row_data, ['target', 'tp', 'take profit'])
            
            return ForexSignal(
                pair=pair,
                signal=signal_type,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                analysis=self._extract_analysis(row_data)
            )
            
        except Exception as e:
            logger.debug(f"Error parsing table row: {e}")
            return None
    
    def _parse_text_signals(self, soup: BeautifulSoup) -> List[ForexSignal]:
        """Parse signals from text content."""
        signals = []
        text_content = soup.get_text()
        
        # Split into paragraphs or sections
        sections = re.split(r'\n\s*\n', text_content)
        
        for section in sections:
            # Look for currency pairs
            for pair in self.all_pairs:
                if pair in section.upper():
                    signal = self._extract_signal_from_text(section, pair)
                    if signal:
                        signals.append(signal)
        
        return signals
    
    def _parse_structured_divs(self, soup: BeautifulSoup) -> List[ForexSignal]:
        """Parse signals from structured div elements."""
        signals = []
        
        # Look for signal cards or containers
        signal_containers = soup.find_all(['div', 'article', 'section'], 
                                        class_=re.compile(r'signal|trade|forex|currency', re.I))
        
        for container in signal_containers:
            signal = self._parse_signal_container(container)
            if signal:
                signals.append(signal)
        
        return signals
    
    def _parse_signal_container(self, container) -> Optional[ForexSignal]:
        """Parse a signal from a container element."""
        try:
            text = container.get_text()
            
            # Find currency pair
            pair = None
            for p in self.all_pairs:
                if p in text.upper():
                    pair = p
                    break
            
            if not pair:
                return None
            
            # Extract signal type
            signal_type = self._detect_signal_type(text)
            
            # Extract prices using regex
            prices = re.findall(r'\d+\.?\d*', text)
            entry_price = float(prices[0]) if prices else None
            stop_loss = None
            take_profit = None
            
            # Look for SL/TP patterns
            sl_match = re.search(r'(?:sl|stop loss)[:\s]*(\d+\.?\d*)', text, re.I)
            tp_match = re.search(r'(?:tp|take profit|target)[:\s]*(\d+\.?\d*)', text, re.I)
            
            if sl_match:
                stop_loss = float(sl_match.group(1))
            if tp_match:
                take_profit = float(tp_match.group(1))
            
            return ForexSignal(
                pair=pair,
                signal=signal_type,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
        except Exception as e:
            logger.debug(f"Error parsing signal container: {e}")
            return None
    
    def _extract_signal_from_text(self, text: str, pair: str, 
                                 context_lines: Optional[List[str]] = None) -> Optional[ForexSignal]:
        """Extract signal details from text content."""
        try:
            # Combine with context if provided
            full_text = text
            if context_lines:
                full_text = '\n'.join(context_lines)
            
            signal_type = self._detect_signal_type(full_text)
            
            # Extract prices
            entry_price = None
            stop_loss = None
            take_profit = None
            
            # Look for price patterns
            price_pattern = r'(\d+\.?\d*)'
            
            # Entry price patterns
            entry_patterns = [
                rf'{pair}.*?@\s*{price_pattern}',
                rf'entry[:\s]*{price_pattern}',
                rf'buy\s+{pair}.*?{price_pattern}',
                rf'sell\s+{pair}.*?{price_pattern}'
            ]
            
            for pattern in entry_patterns:
                match = re.search(pattern, full_text, re.I)
                if match:
                    entry_price = float(match.group(1))
                    break
            
            # SL/TP extraction
            sl_match = re.search(rf'(?:sl|stop loss)[:\s]*{price_pattern}', full_text, re.I)
            tp_match = re.search(rf'(?:tp|take profit|target)[:\s]*{price_pattern}', full_text, re.I)
            
            if sl_match:
                stop_loss = float(sl_match.group(1))
            if tp_match:
                take_profit = float(tp_match.group(1))
            
            return ForexSignal(
                pair=pair,
                signal=signal_type,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                analysis=text[:200]  # First 200 chars as analysis
            )
            
        except Exception as e:
            logger.debug(f"Error extracting signal from text: {e}")
            return None
    
    def _detect_signal_type(self, text: str) -> SignalType:
        """Detect signal type from text content."""
        text_lower = text.lower()
        
        # Count keyword occurrences
        signal_scores = {
            SignalType.BUY: 0,
            SignalType.SELL: 0,
            SignalType.NEUTRAL: 0
        }
        
        for signal_type, keywords in self.SIGNAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    signal_scores[signal_type] += 1
        
        # Return highest scoring signal type
        max_score = max(signal_scores.values())
        if max_score == 0:
            return SignalType.NEUTRAL
        
        for signal_type, score in signal_scores.items():
            if score == max_score:
                return signal_type
        
        return SignalType.NEUTRAL
    
    def _extract_signal_type(self, row_data: Dict[str, str], cells: List) -> SignalType:
        """Extract signal type from row data."""
        # Check specific columns
        for key in ['signal', 'action', 'recommendation', 'direction']:
            if key in row_data:
                return self._detect_signal_type(row_data[key])
        
        # Check all cell text
        all_text = ' '.join(cell.get_text(strip=True) for cell in cells)
        return self._detect_signal_type(all_text)
    
    def _extract_price(self, row_data: Dict[str, str], keys: List[str]) -> Optional[float]:
        """Extract price from row data."""
        for key in keys:
            if key in row_data:
                try:
                    # Extract numeric value
                    price_text = row_data[key]
                    price_match = re.search(r'(\d+\.?\d*)', price_text)
                    if price_match:
                        return float(price_match.group(1))
                except:
                    continue
        return None
    
    def _extract_analysis(self, row_data: Dict[str, str]) -> Optional[str]:
        """Extract analysis or notes from row data."""
        for key in ['analysis', 'notes', 'comment', 'reason']:
            if key in row_data and row_data[key]:
                return row_data[key][:200]  # Limit length
        return None
    
    def _is_valid_pair(self, text: str) -> bool:
        """Check if text is a valid currency pair."""
        # Basic format check
        if '/' not in text:
            return False
        
        parts = text.split('/')
        if len(parts) != 2:
            return False
        
        # Check length
        if len(parts[0]) != 3 or len(parts[1]) != 3:
            # Allow for commodities like XAU/USD
            if not (parts[0] in ['XAU', 'XAG'] or parts[1] in ['XAU', 'XAG']):
                return False
        
        return True
    
    def _deduplicate_signals(self, signals: List[ForexSignal]) -> List[ForexSignal]:
        """Remove duplicate signals based on pair and signal type."""
        seen = set()
        unique_signals = []
        
        for signal in signals:
            key = (signal.pair, signal.signal)
            if key not in seen:
                seen.add(key)
                unique_signals.append(signal)
        
        return unique_signals