"""
Generic table parser for extracting structured data from HTML tables.
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class TableParser:
    """Generic parser for extracting data from HTML tables."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize table parser with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.header_mappings = self.config.get('header_mappings', {})
        self.cell_processors = self.config.get('cell_processors', {})
    
    def parse_table(self, table: Tag, 
                   required_headers: Optional[List[str]] = None,
                   cell_processor: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """
        Parse a single HTML table into structured data.
        
        Args:
            table: BeautifulSoup table element
            required_headers: List of required header names
            cell_processor: Optional function to process cell values
            
        Returns:
            List of dictionaries representing table rows
        """
        try:
            headers = self._extract_headers(table)
            if not headers:
                logger.warning("No headers found in table")
                return []
            
            # Check required headers
            if required_headers:
                missing_headers = set(required_headers) - set(headers)
                if missing_headers:
                    logger.warning(f"Missing required headers: {missing_headers}")
                    return []
            
            # Extract data rows
            rows = self._extract_data_rows(table, headers, cell_processor)
            
            logger.debug(f"Extracted {len(rows)} rows from table")
            return rows
            
        except Exception as e:
            logger.error(f"Error parsing table: {e}")
            return []
    
    def parse_all_tables(self, html_content: str,
                        table_selector: str = 'table',
                        required_headers: Optional[List[str]] = None) -> List[List[Dict[str, Any]]]:
        """
        Parse all tables in HTML content.
        
        Args:
            html_content: Raw HTML content
            table_selector: CSS selector for tables
            required_headers: List of required header names
            
        Returns:
            List of table data (each table is a list of row dictionaries)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        tables = soup.select(table_selector)
        
        all_table_data = []
        for i, table in enumerate(tables):
            table_data = self.parse_table(table, required_headers)
            if table_data:
                all_table_data.append(table_data)
                logger.debug(f"Table {i+1}: {len(table_data)} rows")
        
        return all_table_data
    
    def find_table_by_headers(self, html_content: str, 
                             target_headers: List[str],
                             min_matches: int = 1) -> Optional[List[Dict[str, Any]]]:
        """
        Find and parse a table containing specific headers.
        
        Args:
            html_content: Raw HTML content
            target_headers: Headers to search for
            min_matches: Minimum number of headers that must match
            
        Returns:
            Table data if found, None otherwise
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        tables = soup.find_all('table')
        
        for table in tables:
            headers = self._extract_headers(table)
            if not headers:
                continue
            
            # Check header matches (case insensitive)
            headers_lower = [h.lower() for h in headers]
            target_lower = [h.lower() for h in target_headers]
            
            matches = sum(1 for target in target_lower 
                         if any(target in header for header in headers_lower))
            
            if matches >= min_matches:
                return self.parse_table(table)
        
        logger.warning(f"No table found with headers matching: {target_headers}")
        return None
    
    def _extract_headers(self, table: Tag) -> List[str]:
        """Extract header row from table."""
        headers = []
        
        # Try different header row strategies
        strategies = [
            lambda t: t.find('thead').find('tr').find_all(['th', 'td']) if t.find('thead') else None,
            lambda t: t.find('tr').find_all('th') if t.find('tr') else None,
            lambda t: t.find('tr').find_all(['th', 'td']) if t.find('tr') else None,
        ]
        
        for strategy in strategies:
            try:
                header_cells = strategy(table)
                if header_cells:
                    headers = [self._clean_cell_text(cell) for cell in header_cells]
                    if any(headers):  # At least one non-empty header
                        break
            except:
                continue
        
        # Apply header mappings
        mapped_headers = []
        for header in headers:
            mapped = self.header_mappings.get(header.lower(), header)
            mapped_headers.append(mapped)
        
        return mapped_headers
    
    def _extract_data_rows(self, table: Tag, headers: List[str],
                          cell_processor: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """Extract data rows from table."""
        rows = []
        
        # Find all rows (skip header row)
        all_rows = table.find_all('tr')
        data_rows = all_rows[1:] if len(all_rows) > 1 else all_rows
        
        for row in data_rows:
            cells = row.find_all(['td', 'th'])
            
            if len(cells) == 0:
                continue
            
            # Build row dictionary
            row_data = {}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    cell_text = self._clean_cell_text(cell)
                    
                    # Apply cell processor if provided
                    if cell_processor:
                        try:
                            cell_text = cell_processor(cell_text, headers[i])
                        except:
                            pass
                    
                    # Apply column-specific processors
                    processor = self.cell_processors.get(headers[i])
                    if processor:
                        try:
                            cell_text = processor(cell_text)
                        except:
                            pass
                    
                    row_data[headers[i]] = cell_text
            
            # Only add rows with at least some data
            if any(value for value in row_data.values()):
                rows.append(row_data)
        
        return rows
    
    def _clean_cell_text(self, cell: Tag) -> str:
        """Clean and normalize cell text content."""
        if not cell:
            return ""
        
        # Get text content
        text = cell.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        # Remove common artifacts
        text = text.replace('\n', ' ').replace('\r', ' ')
        text = text.replace('\u00a0', ' ')  # Non-breaking space
        
        return text.strip()
    
    def extract_table_summary(self, table_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract summary statistics from table data."""
        if not table_data:
            return {}
        
        summary = {
            'row_count': len(table_data),
            'columns': list(table_data[0].keys()) if table_data else [],
            'column_count': len(table_data[0]) if table_data else 0
        }
        
        # Analyze column types and values
        column_stats = {}
        for column in summary['columns']:
            values = [row.get(column, '') for row in table_data]
            non_empty_values = [v for v in values if v]
            
            column_stats[column] = {
                'non_empty_count': len(non_empty_values),
                'empty_count': len(values) - len(non_empty_values),
                'unique_values': len(set(non_empty_values)),
                'sample_values': non_empty_values[:3]  # First 3 values as samples
            }
        
        summary['column_stats'] = column_stats
        return summary


class ForexTableParser(TableParser):
    """Specialized parser for forex signal tables."""
    
    def __init__(self):
        config = {
            'header_mappings': {
                'currency': 'pair',
                'symbol': 'pair',
                'instrument': 'pair',
                'action': 'signal',
                'recommendation': 'signal',
                'direction': 'signal',
                'entry': 'entry_price',
                'price': 'entry_price',
                'stop': 'stop_loss',
                'sl': 'stop_loss',
                'target': 'take_profit',
                'tp': 'take_profit',
            },
            'cell_processors': {
                'entry_price': self._parse_price,
                'stop_loss': self._parse_price,
                'take_profit': self._parse_price,
            }
        }
        super().__init__(config)
    
    def _parse_price(self, value: str) -> Optional[float]:
        """Parse price from string value."""
        import re
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


class EarningsTableParser(TableParser):
    """Specialized parser for earnings release tables."""
    
    def __init__(self):
        config = {
            'header_mappings': {
                'symbol': 'ticker',
                'stock': 'ticker',
                'company': 'company_name',
                'date': 'release_date',
                'time': 'release_time',
                'eps': 'eps_estimate',
                'earnings': 'eps_estimate',
                'revenue': 'revenue_estimate',
                'sales': 'revenue_estimate',
            }
        }
        super().__init__(config)