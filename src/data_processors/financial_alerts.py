"""
Financial alerts data processor.
Converts raw scraped content into structured data models.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup, Tag
from datetime import datetime

from .data_models import (
    ForexForecast, StockCryptoForecast, OptionsTrade, 
    SwingTrade, DayTrade, EarningsReport, TableSection,
    StructuredFinancialReport
)

logger = logging.getLogger(__name__)


class FinancialAlertsProcessor:
    """Processes scraped financial data into structured format."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize processor with configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Known forex pairs to look for
        self.forex_pairs = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'USDCAD',
            'AUDUSD', 'NZDUSD', 'EURJPY', 'GBPJPY', 'EURGBP',
            'NZDJPY', 'AUDCAD', 'GBPCAD', 'EURAUD', 'EURNZD'
        ]
        
        # Known options tickers
        self.options_tickers = [
            'QQQ', 'SPY', 'IWM', 'NVDA', 'TSLA', 'AAPL', 'MSFT',
            'GOOGL', 'AMZN', 'META', 'NFLX', 'AMD', 'CRM'
        ]
        
        # Common stock tickers for swing/day trades
        self.stock_tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
            'JPM', 'BAC', 'WMT', 'JNJ', 'PG', 'V', 'MA', 'UNH'
        ]

    def process_scraped_data(self, html_content: str, text_content: str, 
                           source_url: Optional[str] = None) -> StructuredFinancialReport:
        """
        Main method to process all scraped data.
        
        Args:
            html_content: Raw HTML content
            text_content: Plain text content
            source_url: Source URL for reference
            
        Returns:
            StructuredFinancialReport with all parsed data
        """
        logger.info("🔍 Processing scraped data into structured format...")
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Initialize report
        report = StructuredFinancialReport(
            source_url=source_url,
            timestamp=datetime.now()
        )
        
        # Process each section
        report.forex_forecasts = self._extract_forex_forecasts(soup, text_content)
        report.stock_crypto_forecasts = self._extract_stock_crypto_forecasts(soup, text_content)
        report.options_trades = self._extract_options_trades(soup, text_content)
        report.swing_trades = self._extract_swing_trades(soup, text_content)
        report.day_trades = self._extract_day_trades(soup, text_content)
        report.earnings_reports = self._extract_earnings_reports(soup, text_content)
        report.table_sections = self._extract_table_sections(soup)
        
        # Log summary
        stats = report.get_summary_stats()
        logger.info(f"✅ Processed data: {stats['total_entries']} total entries")
        logger.info(f"   📊 Forex: {stats['forex_forecasts']}, Options: {stats['options_trades']}")
        logger.info(f"   📈 Stocks: {stats['stock_crypto_forecasts']}, Earnings: {stats['earnings_reports']}")
        logger.info(f"   🔄 Swing: {stats['swing_trades']}, Day: {stats['day_trades']}")
        
        return report

    def _extract_forex_forecasts(self, soup: BeautifulSoup, text_content: str) -> List[ForexForecast]:
        """Extract forex forecasts from content."""
        logger.info("🔍 Extracting forex forecasts...")
        forecasts = []
        
        lines = text_content.split('\n')
        
        for pair in self.forex_pairs:
            forecast = self._parse_forex_pair(pair, lines, soup)
            if forecast:
                forecasts.append(forecast)
                logger.info(f"✅ Extracted {pair}: {forecast.trade_type}")
        
        return forecasts

    def _parse_forex_pair(self, pair: str, lines: List[str], soup: BeautifulSoup) -> Optional[ForexForecast]:
        """Parse individual forex pair data."""
        try:
            # Find the pair in content
            pair_line_index = None
            for i, line in enumerate(lines):
                if pair in line.upper():
                    pair_line_index = i
                    break
            
            if pair_line_index is None:
                return None
            
            # Extract context around the pair (15 lines after)
            context_start = max(0, pair_line_index - 1)
            context_end = min(len(lines), pair_line_index + 15)
            context_lines = lines[context_start:context_end]
            
            # Initialize data
            high = "N/A"
            average = "N/A" 
            low = "N/A"
            fourteen_day_average = "N/A"
            trade_type = "N/A"
            exit_level = "N/A"
            trade_status = None
            special_badge = None
            
            # Parse each line in context
            for line in context_lines:
                line_upper = line.upper().strip()
                
                # Extract high
                if 'HIGH:' in line_upper:
                    high_match = re.search(r'HIGH:\s*([\d.]+)', line_upper)
                    if high_match:
                        high = high_match.group(1)
                
                # Extract average
                if 'AVERAGE:' in line_upper:
                    avg_match = re.search(r'AVERAGE:\s*([\d.]+)', line_upper)
                    if avg_match:
                        average = avg_match.group(1)
                
                # Extract low
                if 'LOW:' in line_upper:
                    low_match = re.search(r'LOW:\s*([\d.]+)', line_upper)
                    if low_match:
                        low = low_match.group(1)
                
                # Extract 14 day average
                if '14 DAY' in line_upper or 'PIPS' in line_upper:
                    if any(x in line_upper for x in ['AVERAGE', 'PIPS']):
                        # Extract PIPS value or range
                        pips_match = re.search(r'(\d+(?:\s*-\s*\d+)?)\s*PIPS', line_upper)
                        if pips_match:
                            fourteen_day_average = f"{pips_match.group(1)} PIPS"
                
                # Extract trade type (MT4 BUY/SELL)
                if 'MT4' in line_upper:
                    if 'BUY' in line_upper:
                        buy_match = re.search(r'MT4\s+BUY\s*[<>]\s*([\d.]+)', line_upper)
                        if buy_match:
                            trade_type = f"MT4 BUY < {buy_match.group(1)}"
                    elif 'SELL' in line_upper:
                        sell_match = re.search(r'MT4\s+SELL\s*[<>]\s*([\d.]+)', line_upper)
                        if sell_match:
                            trade_type = f"MT4 SELL < {sell_match.group(1)}"
                
                # Extract exit level
                if 'EXIT:' in line_upper:
                    exit_match = re.search(r'EXIT:?\s*([\d.]+)', line_upper)
                    if exit_match:
                        exit_level = exit_match.group(1)
                
                # Extract trade status
                if 'TRADE IN PROFIT' in line_upper:
                    trade_status = "TRADE IN PROFIT"
                elif 'PROFIT' in line_upper and 'TRADE' in line_upper:
                    trade_status = "TRADE IN PROFIT"
                
                # Extract special badge
                if 'NEW!' in line_upper:
                    special_badge = "NEW!"
            
            # Only create forecast if we have meaningful data
            if trade_type != "N/A" or any(x != "N/A" for x in [high, average, low]):
                return ForexForecast(
                    pair=pair,
                    high=high,
                    average=average,
                    low=low,
                    fourteen_day_average=fourteen_day_average,
                    trade_type=trade_type,
                    exit=exit_level,
                    trade_status=trade_status,
                    special_badge=special_badge
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing forex pair {pair}: {e}")
            return None

    def _extract_stock_crypto_forecasts(self, soup: BeautifulSoup, text_content: str) -> List[StockCryptoForecast]:
        """Extract stock & crypto forecasts from content."""
        logger.info("🔍 Extracting stock & crypto forecasts...")
        forecasts = []
        
        # Look for stock/crypto patterns in text
        lines = text_content.split('\n')
        
        for ticker in self.stock_tickers:
            forecast = self._parse_stock_crypto(ticker, lines)
            if forecast:
                forecasts.append(forecast)
                logger.info(f"✅ Extracted stock/crypto {ticker}: {forecast.direction}")
        
        return forecasts

    def _parse_stock_crypto(self, ticker: str, lines: List[str]) -> Optional[StockCryptoForecast]:
        """Parse individual stock/crypto data."""
        try:
            # Find ticker in content
            ticker_line_index = None
            for i, line in enumerate(lines):
                if ticker in line.upper() and any(x in line.upper() for x in ['BUY', 'SELL', 'LONG', 'SHORT']):
                    ticker_line_index = i
                    break
            
            if ticker_line_index is None:
                return None
            
            # Get context
            context_start = max(0, ticker_line_index - 2)
            context_end = min(len(lines), ticker_line_index + 10)
            context_lines = lines[context_start:context_end]
            
            direction = "N/A"
            entry = "N/A"
            take_profit = "N/A"
            stop_loss = "N/A"
            status = "N/A"
            
            for line in context_lines:
                line_upper = line.upper().strip()
                
                # Extract direction
                if 'BUY' in line_upper or 'LONG' in line_upper:
                    direction = "BUY"
                elif 'SELL' in line_upper or 'SHORT' in line_upper:
                    direction = "SELL"
                
                # Extract entry price
                if 'ENTRY' in line_upper:
                    entry_match = re.search(r'ENTRY:?\s*\$?([\d.]+)', line_upper)
                    if entry_match:
                        entry = entry_match.group(1)
                
                # Extract take profit
                if 'TAKE PROFIT' in line_upper or 'TP' in line_upper:
                    tp_match = re.search(r'(?:TAKE PROFIT|TP):?\s*\$?([\d.]+)', line_upper)
                    if tp_match:
                        take_profit = tp_match.group(1)
                
                # Extract stop loss
                if 'STOP LOSS' in line_upper or 'SL' in line_upper:
                    sl_match = re.search(r'(?:STOP LOSS|SL):?\s*\$?([\d.]+)', line_upper)
                    if sl_match:
                        stop_loss = sl_match.group(1)
                
                # Extract status
                if 'ACTIVE' in line_upper:
                    status = "ACTIVE"
                elif 'CLOSED' in line_upper:
                    status = "CLOSED"
                elif 'PROFIT' in line_upper:
                    status = "IN PROFIT"
            
            if direction != "N/A":
                return StockCryptoForecast(
                    ticker=ticker,
                    direction=direction,
                    entry=entry,
                    take_profit=take_profit,
                    stop_loss=stop_loss,
                    status=status
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing stock/crypto {ticker}: {e}")
            return None

    def _extract_options_trades(self, soup: BeautifulSoup, text_content: str) -> List[OptionsTrade]:
        """Extract options trades from content."""
        logger.info("🔍 Extracting options trades...")
        trades = []
        
        lines = text_content.split('\n')
        
        for ticker in self.options_tickers:
            trade = self._parse_options_trade(ticker, lines)
            if trade:
                trades.append(trade)
                logger.info(f"✅ Extracted options {ticker}: CALL {trade.call_strike}, PUT {trade.put_strike}")
        
        return trades

    def _parse_options_trade(self, ticker: str, lines: List[str]) -> Optional[OptionsTrade]:
        """Parse individual options trade data."""
        try:
            # Find ticker in content
            ticker_line_index = None
            for i, line in enumerate(lines):
                if ticker in line.upper():
                    ticker_line_index = i
                    break
            
            if ticker_line_index is None:
                return None
            
            # Get larger context for options data
            context_start = max(0, ticker_line_index - 1)
            context_end = min(len(lines), ticker_line_index + 20)
            context_lines = lines[context_start:context_end]
            
            fifty_two_week_high = "N/A"
            fifty_two_week_low = "N/A"
            call_strike = "N/A"
            put_strike = "N/A"
            trade_status = None
            special_badge = None
            
            for line in context_lines:
                line_upper = line.upper().strip()
                
                # Extract 52 week high
                if '52 WEEK HIGH:' in line_upper:
                    high_match = re.search(r'52 WEEK HIGH:\s*([\d.]+)', line_upper)
                    if high_match:
                        fifty_two_week_high = high_match.group(1)
                
                # Extract 52 week low
                if '52 WEEK LOW:' in line_upper:
                    low_match = re.search(r'52 WEEK LOW:\s*([\d.]+)', line_upper)
                    if low_match:
                        fifty_two_week_low = low_match.group(1)
                
                # Extract strike prices - look for pattern "CALL > 352.42"
                if 'CALL' in line_upper and '>' in line_upper:
                    call_match = re.search(r'CALL\s*>\s*([\d.]+)', line_upper)
                    if call_match:
                        call_strike = f"CALL > {call_match.group(1)}"
                
                if 'PUT' in line_upper and '<' in line_upper:
                    put_match = re.search(r'PUT\s*<\s*([\d.]+)', line_upper)
                    if put_match:
                        put_strike = f"PUT < {put_match.group(1)}"
                
                # Also check for combined strike price line
                if 'STRIKE PRICE:' in line_upper:
                    # Look for both CALL and PUT in same line
                    call_match = re.search(r'CALL\s*>\s*([\d.]+)', line_upper)
                    put_match = re.search(r'PUT\s*<\s*([\d.]+)', line_upper)
                    
                    if call_match:
                        call_strike = f"CALL > {call_match.group(1)}"
                    if put_match:
                        put_strike = f"PUT < {put_match.group(1)}"
                
                # Extract trade status
                if 'TRADE IN PROFIT' in line_upper:
                    trade_status = "trade in profit"
                elif 'PROFIT' in line_upper:
                    trade_status = "profit"
                
                # Extract special badge
                if 'NEW!' in line_upper:
                    special_badge = "NEW!"
            
            # Only create trade if we have strike prices or 52-week data
            if call_strike != "N/A" or put_strike != "N/A" or fifty_two_week_high != "N/A":
                return OptionsTrade(
                    ticker=ticker,
                    fifty_two_week_high=fifty_two_week_high,
                    fifty_two_week_low=fifty_two_week_low,
                    call_strike=call_strike,
                    put_strike=put_strike,
                    trade_status=trade_status,
                    special_badge=special_badge
                )
            
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing options trade {ticker}: {e}")
            return None

    def _extract_swing_trades(self, soup: BeautifulSoup, text_content: str) -> List[SwingTrade]:
        """Extract premium swing trades from content."""
        logger.info("🔍 Extracting swing trades...")
        return self._extract_premium_trades(text_content, "Premium Swing Trades", SwingTrade)

    def _extract_day_trades(self, soup: BeautifulSoup, text_content: str) -> List[DayTrade]:
        """Extract premium day trades from content."""
        logger.info("🔍 Extracting day trades...")
        return self._extract_premium_trades(text_content, "Premium Day Trades", DayTrade)

    def _extract_earnings_reports(self, soup: BeautifulSoup, text_content: str) -> List[EarningsReport]:
        """Extract earnings reports from content."""
        logger.info("🔍 Extracting earnings reports...")
        return self._extract_premium_trades(text_content, "Most Anticipated Earnings Releases", EarningsReport)

    def _extract_premium_trades(self, text_content: str, section_name: str, model_class) -> List:
        """Extract premium trades/earnings from specific section."""
        trades = []
        lines = text_content.split('\n')
        
        # Find the section
        section_start = None
        for i, line in enumerate(lines):
            if section_name in line:
                section_start = i
                break
        
        if section_start is None:
            return trades
        
        # Parse entries in the section (look ahead 50 lines)
        section_end = min(len(lines), section_start + 50)
        section_lines = lines[section_start:section_end]
        
        i = 0
        while i < len(section_lines):
            line = section_lines[i].strip()
            
            # Look for company pattern: "Company Name (TICKER)"
            company_match = re.match(r'^(.+?)\s*\(([A-Z]+)\)$', line)
            
            if company_match:
                company_name = company_match.group(1).strip()
                ticker = company_match.group(2)
                
                # Extract data from following lines
                trade_data = {
                    'company': company_name,
                    'ticker': ticker,
                    'earnings_date': 'N/A',
                    'current_price': 'N/A',
                    'rationale': 'N/A'
                }
                
                # Look ahead for trade data
                for j in range(1, min(8, len(section_lines) - i)):
                    next_line = section_lines[i + j].strip()
                    
                    if 'Earnings Report:' in next_line:
                        trade_data['earnings_date'] = next_line.replace('Earnings Report:', '').strip()
                    elif 'Current Price:' in next_line:
                        trade_data['current_price'] = next_line.replace('Current Price:', '').strip()
                    elif 'Rationale:' in next_line:
                        rationale = next_line.replace('Rationale:', '').strip()
                        
                        # Rationale might continue on next lines
                        for k in range(j + 1, min(j + 3, len(section_lines) - i)):
                            if section_lines[i + k].strip() and not any(keyword in section_lines[i + k] for keyword in ['Earnings Report:', 'Current Price:', 'Rationale:']):
                                rationale += ' ' + section_lines[i + k].strip()
                            else:
                                break
                        
                        trade_data['rationale'] = rationale
                
                # Only add if we found real data
                if trade_data['earnings_date'] != 'N/A' or trade_data['current_price'] != 'N/A':
                    trade = model_class(**trade_data)
                    trades.append(trade)
                    logger.info(f"✅ Extracted {section_name.lower()} for {ticker}")
            
            i += 1
        
        return trades

    def _extract_table_sections(self, soup: BeautifulSoup) -> List[TableSection]:
        """Extract table sections from HTML."""
        logger.info("🔍 Extracting table sections...")
        table_sections = []
        
        # Find all tables
        tables = soup.find_all('table')
        
        for i, table in enumerate(tables):
            try:
                # Extract table title (look for heading before table)
                title = f"Table {i + 1}"
                
                # Look for preceding heading
                prev_sibling = table.find_previous_sibling(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if prev_sibling:
                    title = prev_sibling.get_text().strip()
                
                # Extract headers
                headers = []
                header_row = table.find('tr')
                if header_row:
                    for th in header_row.find_all(['th', 'td']):
                        headers.append(th.get_text().strip())
                
                # Extract data rows
                rows = []
                for row in table.find_all('tr')[1:]:  # Skip header row
                    row_data = []
                    for cell in row.find_all(['td', 'th']):
                        row_data.append(cell.get_text().strip())
                    if row_data:
                        rows.append(row_data)
                
                if headers and rows:
                    table_section = TableSection(
                        title=title,
                        headers=headers,
                        rows=rows
                    )
                    table_sections.append(table_section)
                    logger.info(f"✅ Extracted table: {title} ({len(rows)} rows)")
                    
            except Exception as e:
                logger.warning(f"Error processing table {i}: {e}")
        
        return table_sections

    def validate_report(self, report: StructuredFinancialReport) -> Tuple[bool, List[str]]:
        """
        Validate the generated report for completeness and accuracy.
        
        Args:
            report: Generated report to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check if report has any data
        stats = report.get_summary_stats()
        if stats['total_entries'] == 0:
            issues.append("Report contains no data entries")
        
        # Validate forex forecasts
        for forex in report.forex_forecasts:
            if forex.trade_type == "N/A" and forex.high == "N/A":
                issues.append(f"Forex {forex.pair} has insufficient data")
        
        # Validate options trades
        for option in report.options_trades:
            if option.call_strike == "N/A" and option.put_strike == "N/A":
                issues.append(f"Options {option.ticker} missing strike prices")
        
        # Check for reasonable data counts
        if stats['forex_forecasts'] > 50:
            issues.append(f"Unusually high forex count: {stats['forex_forecasts']}")
        
        if stats['options_trades'] > 20:
            issues.append(f"Unusually high options count: {stats['options_trades']}")
        
        is_valid = len(issues) == 0
        return is_valid, issues