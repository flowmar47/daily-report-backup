"""
Earnings release parser for extracting earnings calendar data.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from ..data_models import EarningsRelease

logger = logging.getLogger(__name__)


class EarningsParser:
    """Parser for extracting earnings release information."""
    
    # Time indicators
    TIME_MAPPINGS = {
        'bmo': 'BMO',
        'before market open': 'BMO',
        'before open': 'BMO',
        'pre-market': 'BMO',
        'amc': 'AMC',
        'after market close': 'AMC',
        'after close': 'AMC',
        'after hours': 'AMC',
        'post-market': 'AMC',
        'during market': 'DMH',
        'market hours': 'DMH',
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize earnings parser with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.max_releases = self.config.get('max_releases', 20)
    
    def parse_html_content(self, html_content: str) -> List[EarningsRelease]:
        """
        Parse earnings releases from HTML content.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            List of EarningsRelease objects
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        releases = []
        
        # Try multiple parsing strategies
        releases.extend(self._parse_earnings_tables(soup))
        releases.extend(self._parse_earnings_lists(soup))
        releases.extend(self._parse_earnings_text(soup))
        
        # Remove duplicates and limit results
        unique_releases = self._deduplicate_releases(releases)
        
        if len(unique_releases) > self.max_releases:
            unique_releases = unique_releases[:self.max_releases]
        
        logger.info(f"Parsed {len(unique_releases)} earnings releases")
        return unique_releases
    
    def parse_text_content(self, text_content: str) -> List[EarningsRelease]:
        """
        Parse earnings releases from plain text content.
        
        Args:
            text_content: Plain text content
            
        Returns:
            List of EarningsRelease objects
        """
        releases = []
        lines = text_content.split('\n')
        
        for line in lines:
            release = self._parse_earnings_line(line.strip())
            if release:
                releases.append(release)
        
        return self._deduplicate_releases(releases)
    
    def _parse_earnings_tables(self, soup: BeautifulSoup) -> List[EarningsRelease]:
        """Parse earnings from HTML tables."""
        releases = []
        
        # Find tables that might contain earnings data
        tables = soup.find_all('table')
        
        for table in tables:
            # Check if table contains earnings-related headers
            headers = []
            header_row = table.find('tr')
            if header_row:
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
            
            # Look for earnings-related keywords in headers
            earnings_keywords = ['ticker', 'symbol', 'company', 'earnings', 'eps', 'revenue', 'date', 'time']
            if any(keyword in ' '.join(headers) for keyword in earnings_keywords):
                table_releases = self._parse_earnings_table(table, headers)
                releases.extend(table_releases)
        
        return releases
    
    def _parse_earnings_table(self, table, headers: List[str]) -> List[EarningsRelease]:
        """Parse earnings from a specific table."""
        releases = []
        
        # Map headers to standard fields
        header_mapping = self._create_header_mapping(headers)
        
        # Parse data rows
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                release = self._parse_table_row(cells, header_mapping)
                if release:
                    releases.append(release)
        
        return releases
    
    def _parse_table_row(self, cells: List, header_mapping: Dict[int, str]) -> Optional[EarningsRelease]:
        """Parse a single table row into an earnings release."""
        try:
            row_data = {}
            
            # Extract data based on header mapping
            for i, cell in enumerate(cells):
                if i in header_mapping:
                    field = header_mapping[i]
                    value = cell.get_text(strip=True)
                    row_data[field] = value
            
            # Must have at least ticker
            if 'ticker' not in row_data:
                return None
            
            ticker = self._normalize_ticker(row_data['ticker'])
            if not ticker:
                return None
            
            return EarningsRelease(
                ticker=ticker,
                company_name=row_data.get('company_name'),
                release_date=self._normalize_date(row_data.get('release_date')),
                release_time=self._normalize_time(row_data.get('release_time')),
                eps_estimate=self._parse_float(row_data.get('eps_estimate')),
                revenue_estimate=self._parse_float(row_data.get('revenue_estimate')),
                notes=row_data.get('notes')
            )
            
        except Exception as e:
            logger.debug(f"Error parsing table row: {e}")
            return None
    
    def _parse_earnings_lists(self, soup: BeautifulSoup) -> List[EarningsRelease]:
        """Parse earnings from list elements."""
        releases = []
        
        # Look for lists that might contain earnings
        lists = soup.find_all(['ul', 'ol', 'div'], class_=re.compile(r'earnings|calendar|release', re.I))
        
        for list_elem in lists:
            items = list_elem.find_all(['li', 'div', 'p'])
            
            for item in items:
                text = item.get_text(strip=True)
                release = self._parse_earnings_text_item(text)
                if release:
                    releases.append(release)
        
        return releases
    
    def _parse_earnings_text(self, soup: BeautifulSoup) -> List[EarningsRelease]:
        """Parse earnings from general text content."""
        releases = []
        
        # Get all text and look for earnings patterns
        text_content = soup.get_text()
        lines = text_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if len(line) > 10:  # Skip very short lines
                release = self._parse_earnings_line(line)
                if release:
                    releases.append(release)
        
        return releases
    
    def _parse_earnings_line(self, line: str) -> Optional[EarningsRelease]:
        """Parse a single line of text for earnings information."""
        # Look for ticker patterns
        ticker_match = re.search(r'\b([A-Z]{1,5})\b', line)
        if not ticker_match:
            return None
        
        ticker = ticker_match.group(1)
        
        # Validate ticker (exclude common words)
        excluded_words = {'EARNINGS', 'BEFORE', 'AFTER', 'MARKET', 'OPEN', 'CLOSE', 'TIME', 'DATE', 'EPS', 'EST'}
        if ticker in excluded_words:
            return None
        
        # Extract other information
        release_time = self._extract_time_from_text(line)
        release_date = self._extract_date_from_text(line)
        eps_estimate = self._extract_eps_from_text(line)
        company_name = self._extract_company_from_text(line, ticker)
        
        return EarningsRelease(
            ticker=ticker,
            company_name=company_name,
            release_date=release_date,
            release_time=release_time,
            eps_estimate=eps_estimate,
            notes=line[:100] if len(line) > 20 else None
        )
    
    def _parse_earnings_text_item(self, text: str) -> Optional[EarningsRelease]:
        """Parse earnings from a structured text item."""
        # This is similar to _parse_earnings_line but for structured items
        return self._parse_earnings_line(text)
    
    def _create_header_mapping(self, headers: List[str]) -> Dict[int, str]:
        """Create mapping from column index to field name."""
        mapping = {}
        
        field_keywords = {
            'ticker': ['ticker', 'symbol', 'stock'],
            'company_name': ['company', 'name', 'corp'],
            'release_date': ['date', 'when', 'day'],
            'release_time': ['time', 'bmo', 'amc', 'before', 'after'],
            'eps_estimate': ['eps', 'earnings', 'estimate'],
            'revenue_estimate': ['revenue', 'sales', 'income'],
        }
        
        for i, header in enumerate(headers):
            header_lower = header.lower()
            
            for field, keywords in field_keywords.items():
                if any(keyword in header_lower for keyword in keywords):
                    mapping[i] = field
                    break
        
        return mapping
    
    def _normalize_ticker(self, ticker: str) -> Optional[str]:
        """Normalize and validate ticker symbol."""
        if not ticker:
            return None
        
        # Clean ticker
        ticker = re.sub(r'[^A-Z]', '', ticker.upper())
        
        # Validate length
        if not (1 <= len(ticker) <= 5):
            return None
        
        return ticker
    
    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Normalize date string."""
        if not date_str:
            return None
        
        # Try to parse common date formats
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{2,4})',  # MM/DD/YYYY or MM/DD/YY
            r'(\d{1,2})-(\d{1,2})-(\d{2,4})',  # MM-DD-YYYY
            r'(\w{3})\s+(\d{1,2})',            # Jan 15
            r'(\d{1,2})\s+(\w{3})',            # 15 Jan
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                return match.group(0)
        
        return date_str.strip()[:20]  # Fallback to first 20 chars
    
    def _normalize_time(self, time_str: str) -> Optional[str]:
        """Normalize time string."""
        if not time_str:
            return None
        
        time_lower = time_str.lower().strip()
        
        # Check against known mappings
        for pattern, normalized in self.TIME_MAPPINGS.items():
            if pattern in time_lower:
                return normalized
        
        return time_str.strip()[:10]  # Fallback to first 10 chars
    
    def _extract_time_from_text(self, text: str) -> Optional[str]:
        """Extract release time from text."""
        text_lower = text.lower()
        
        for pattern, normalized in self.TIME_MAPPINGS.items():
            if pattern in text_lower:
                return normalized
        
        return None
    
    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """Extract release date from text."""
        # Look for date patterns
        date_patterns = [
            r'(\w{3})\s+(\d{1,2})',  # Jan 15
            r'(\d{1,2})/(\d{1,2})',  # 1/15
            r'today|tomorrow|this week|next week'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_eps_from_text(self, text: str) -> Optional[float]:
        """Extract EPS estimate from text."""
        # Look for EPS patterns
        eps_patterns = [
            r'eps[:\s]+\$?(\d+\.?\d*)',
            r'earnings[:\s]+\$?(\d+\.?\d*)',
            r'\$(\d+\.?\d*)\s+eps',
        ]
        
        for pattern in eps_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue
        
        return None
    
    def _extract_company_from_text(self, text: str, ticker: str) -> Optional[str]:
        """Extract company name from text."""
        # Remove ticker from text and look for potential company name
        text_without_ticker = text.replace(ticker, '').strip()
        
        # Look for capitalized words that might be company name
        words = text_without_ticker.split()
        company_words = []
        
        for word in words:
            # Skip common non-company words
            if word.lower() in ['earnings', 'reports', 'before', 'after', 'market', 'eps', 'revenue']:
                break
            if word[0].isupper() and len(word) > 2:
                company_words.append(word)
            elif company_words:  # Stop after first non-capitalized word
                break
        
        if company_words:
            return ' '.join(company_words[:3])  # Max 3 words
        
        return None
    
    def _parse_float(self, value: str) -> Optional[float]:
        """Parse float from string value."""
        if not value:
            return None
        
        # Extract numeric value
        match = re.search(r'(\d+\.?\d*)', value)
        if match:
            try:
                return float(match.group(1))
            except:
                pass
        
        return None
    
    def _deduplicate_releases(self, releases: List[EarningsRelease]) -> List[EarningsRelease]:
        """Remove duplicate earnings releases."""
        seen_tickers = set()
        unique_releases = []
        
        for release in releases:
            if release.ticker not in seen_tickers:
                seen_tickers.add(release.ticker)
                unique_releases.append(release)
        
        return unique_releases