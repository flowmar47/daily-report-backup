#!/usr/bin/env python3
"""
Fixed MyMama Scraper - Parses exact format as shown by user
FOREX PAIRS: High/Average/Low/MT4 Action/Exit
EQUITIES AND OPTIONS: 52 Week High/Low/CALL>/PUT</Status
PREMIUM SWING TRADES: Company names, earnings dates, analysis
"""

import asyncio
import os
import sys
import logging
import json
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
load_dotenv(env_path)

class FixedMyMamaScraper:
    """Fixed MyMama scraper that parses the exact format you specified"""
    
    def __init__(self):
        self.username = os.getenv('MYMAMA_USERNAME')
        self.password = os.getenv('MYMAMA_PASSWORD')
        
        if not self.username or not self.password:
            raise ValueError("Missing MyMama credentials in .env file")
        
        self.target_url = 'https://www.mymama.uk/copy-of-alerts-essentials-1'
        
        # Create output directories
        self.output_dir = script_dir / 'real_alerts_only'
        self.output_dir.mkdir(exist_ok=True)
    
    async def get_real_alerts(self):
        """Get real alerts using working scraper integration"""
        try:
            # Use the working real_only_mymama_scraper as base
            from real_only_mymama_scraper import RealOnlyMyMamaScraper
            
            base_scraper = RealOnlyMyMamaScraper()
            raw_data = await base_scraper.get_real_alerts_only()
            
            if not raw_data.get('has_real_data'):
                logger.warning("No real data from base scraper")
                return self._empty_result()
            
            # Get the latest saved content for parsing
            latest_files = list(self.output_dir.glob('essentials_text_*.txt'))
            if not latest_files:
                logger.warning("No content files found for parsing")
                return self._empty_result()
            
            # Use the most recent file
            latest_file = max(latest_files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_file, 'r') as f:
                page_text = f.read()
            
            logger.info(f"Parsing content from: {latest_file}")
            
            # Parse the content using the exact format you specified
            parsed_data = self._parse_mymama_format(page_text)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error getting real alerts: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_result()
    
    def _parse_mymama_format(self, page_text):
        """Parse MyMama content in the exact format you specified"""
        logger.info("Parsing MyMama content for exact format...")
        
        result = {
            'forex_pairs': {},
            'equities_options': [],
            'premium_swing_trades': [],
            'premium_day_trades': [],
            'has_real_data': False,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Parse FOREX PAIRS section
            forex_data = self._extract_forex_pairs(page_text)
            result['forex_pairs'] = forex_data
            
            # Parse EQUITIES AND OPTIONS section
            options_data = self._extract_equities_options(page_text)
            result['equities_options'] = options_data
            
            # Parse PREMIUM SWING TRADES section
            swing_trades = self._extract_premium_trades(page_text, "PREMIUM SWING TRADES")
            result['premium_swing_trades'] = swing_trades
            
            # Parse PREMIUM DAY TRADES section
            day_trades = self._extract_premium_trades(page_text, "PREMIUM DAY TRADES")
            result['premium_day_trades'] = day_trades
            
            # Check if we have real data
            has_data = bool(forex_data or options_data or swing_trades or day_trades)
            result['has_real_data'] = has_data
            
            if has_data:
                logger.info(f"✅ Parsed real data: {len(forex_data)} forex pairs, {len(options_data)} options, {len(swing_trades)} swing trades, {len(day_trades)} day trades")
                
                # Save parsed result
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = self.output_dir / f'parsed_mymama_{timestamp}.json'
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                # Save latest
                with open(self.output_dir / 'latest_parsed_mymama.json', 'w') as f:
                    json.dump(result, f, indent=2)
            else:
                logger.warning("No real data found in content")
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing MyMama format: {e}")
            import traceback
            traceback.print_exc()
            return self._empty_result()
    
    def _extract_forex_pairs(self, text):
        """Extract FOREX PAIRS in format: High/Average/Low/MT4 Action/Exit"""
        forex_pairs = {}
        
        try:
            # Look for FOREX PAIRS section
            lines = text.split('\n')
            in_forex_section = False
            current_pair = None
            
            for line in lines:
                line_stripped = line.strip()
                line_upper = line_stripped.upper()
                
                # Check if we're entering forex section
                if 'FOREX PAIRS' in line_upper:
                    in_forex_section = True
                    logger.info("Found FOREX PAIRS section")
                    continue
                
                # Check if we're leaving forex section
                if in_forex_section and any(section in line_upper for section in ['PREMIUM', 'EQUITIES', 'OPTIONS']):
                    in_forex_section = False
                    break
                
                if in_forex_section:
                    # Look for currency pair
                    pair_match = re.search(r'Pair:\s*([A-Z]{6})', line_upper)
                    if pair_match:
                        current_pair = pair_match.group(1)
                        forex_pairs[current_pair] = {'pair': current_pair}
                        continue
                    
                    if current_pair and current_pair in forex_pairs:
                        # Extract High
                        high_match = re.search(r'High:\s*([\d.]+)', line_stripped)
                        if high_match:
                            forex_pairs[current_pair]['high'] = high_match.group(1)
                        
                        # Extract Average
                        avg_match = re.search(r'Average:\s*([\d.]+)', line_stripped)
                        if avg_match:
                            forex_pairs[current_pair]['average'] = avg_match.group(1)
                        
                        # Extract Low
                        low_match = re.search(r'Low:\s*([\d.]+)', line_stripped)
                        if low_match:
                            forex_pairs[current_pair]['low'] = low_match.group(1)
                        
                        # Extract MT4 Action
                        mt4_match = re.search(r'MT4 Action:\s*(MT4\s+(?:BUY|SELL))', line_stripped)
                        if mt4_match:
                            forex_pairs[current_pair]['mt4_action'] = mt4_match.group(1)
                        
                        # Extract Exit
                        exit_match = re.search(r'Exit:\s*([\d.]+|TBD)', line_stripped)
                        if exit_match:
                            forex_pairs[current_pair]['exit'] = exit_match.group(1)
            
            logger.info(f"Extracted {len(forex_pairs)} forex pairs")
            return forex_pairs
            
        except Exception as e:
            logger.error(f"Error extracting forex pairs: {e}")
            return {}
    
    def _extract_equities_options(self, text):
        """Extract EQUITIES AND OPTIONS in format: Symbol/52 Week High/Low/CALL>/PUT</Status"""
        options_data = []
        
        try:
            lines = text.split('\n')
            in_options_section = False
            current_symbol = None
            current_option = {}
            
            for line in lines:
                line_stripped = line.strip()
                line_upper = line_stripped.upper()
                
                # Check if we're entering options section
                if 'EQUITIES AND OPTIONS' in line_upper:
                    in_options_section = True
                    logger.info("Found EQUITIES AND OPTIONS section")
                    continue
                
                # Check if we're leaving options section
                if in_options_section and any(section in line_upper for section in ['PREMIUM', 'FOREX']):
                    # Save last option if exists
                    if current_option and current_symbol:
                        options_data.append(current_option)
                    in_options_section = False
                    break
                
                if in_options_section:
                    # Look for Symbol
                    symbol_match = re.search(r'Symbol:\s*([A-Z]+)', line_stripped)
                    if symbol_match:
                        # Save previous option if exists
                        if current_option and current_symbol:
                            options_data.append(current_option)
                        
                        current_symbol = symbol_match.group(1)
                        current_option = {'symbol': current_symbol}
                        continue
                    
                    if current_symbol and current_option:
                        # Extract 52 Week High
                        high_52w_match = re.search(r'52 Week High:\s*([\d.]+)', line_stripped)
                        if high_52w_match:
                            current_option['52_week_high'] = high_52w_match.group(1)
                        
                        # Extract 52 Week Low
                        low_52w_match = re.search(r'52 Week Low:\s*([\d.]+)', line_stripped)
                        if low_52w_match:
                            current_option['52_week_low'] = low_52w_match.group(1)
                        
                        # Extract CALL
                        call_match = re.search(r'CALL\s*>\s*([\d.]+)', line_stripped)
                        if call_match:
                            current_option['call_strike'] = call_match.group(1)
                        elif 'CALL > N/A' in line_stripped:
                            current_option['call_strike'] = 'N/A'
                        
                        # Extract PUT
                        put_match = re.search(r'PUT\s*<\s*([\d.]+)', line_stripped)
                        if put_match:
                            current_option['put_strike'] = put_match.group(1)
                        elif 'PUT < N/A' in line_stripped:
                            current_option['put_strike'] = 'N/A'
                        
                        # Extract Status
                        if 'Status:' in line_stripped:
                            status_match = re.search(r'Status:\s*(.+)', line_stripped)
                            if status_match:
                                current_option['status'] = status_match.group(1).strip()
            
            # Don't forget the last option
            if current_option and current_symbol:
                options_data.append(current_option)
            
            logger.info(f"Extracted {len(options_data)} options")
            return options_data
            
        except Exception as e:
            logger.error(f"Error extracting options: {e}")
            return []
    
    def _extract_premium_trades(self, text, section_name):
        """Extract PREMIUM SWING TRADES or PREMIUM DAY TRADES sections"""
        trades = []
        
        try:
            lines = text.split('\n')
            in_section = False
            current_trade = {}
            
            for line in lines:
                line_stripped = line.strip()
                line_upper = line_stripped.upper()
                
                # Check if we're entering the section
                if section_name.upper() in line_upper:
                    in_section = True
                    logger.info(f"Found {section_name} section")
                    continue
                
                # Check if we're leaving the section
                if in_section and any(keyword in line_upper for keyword in ['PREMIUM', 'EQUITIES', 'FOREX']) and section_name.upper() not in line_upper:
                    # Save last trade if exists
                    if current_trade:
                        trades.append(current_trade)
                    in_section = False
                    break
                
                if in_section and line_stripped:
                    # Look for company ticker and name
                    company_match = re.search(r'^([A-Z]{2,5})\s*[-–]\s*(.+)', line_stripped)
                    if company_match:
                        # Save previous trade if exists
                        if current_trade:
                            trades.append(current_trade)
                        
                        ticker = company_match.group(1)
                        company_name = company_match.group(2).strip()
                        current_trade = {
                            'ticker': ticker,
                            'company_name': company_name,
                            'analysis': [],
                            'earnings_date': None,
                            'strategy': None
                        }
                        continue
                    
                    # Look for earnings date
                    earnings_match = re.search(r'EARNINGS DATE:\s*(.+)', line_stripped)
                    if earnings_match and current_trade:
                        current_trade['earnings_date'] = earnings_match.group(1).strip()
                        continue
                    
                    # Look for analysis
                    analysis_match = re.search(r'ANALYSIS:\s*(.+)', line_stripped)
                    if analysis_match and current_trade:
                        current_trade['analysis'].append(analysis_match.group(1).strip())
                        continue
                    
                    # Look for strategy
                    strategy_match = re.search(r'STRATEGY:\s*(.+)', line_stripped)
                    if strategy_match and current_trade:
                        current_trade['strategy'] = strategy_match.group(1).strip()
                        continue
                    
                    # Add other lines as analysis if we have a current trade
                    if current_trade and line_stripped and not line_stripped.startswith(('Monday', 'Tuesday', 'Wednesday')):
                        current_trade['analysis'].append(line_stripped)
            
            # Don't forget the last trade
            if current_trade:
                trades.append(current_trade)
            
            logger.info(f"Extracted {len(trades)} {section_name.lower()}")
            return trades
            
        except Exception as e:
            logger.error(f"Error extracting {section_name}: {e}")
            return []
    
    def _empty_result(self):
        """Return empty result structure"""
        return {
            'forex_pairs': {},
            'equities_options': [],
            'premium_swing_trades': [],
            'premium_day_trades': [],
            'has_real_data': False,
            'timestamp': datetime.now().isoformat(),
            'message': 'No real data available'
        }
    
    def format_output(self, data):
        """Format the parsed data into the exact output format you specified"""
        output_lines = []
        
        if data.get('forex_pairs'):
            output_lines.append("FOREX PAIRS")
            output_lines.append("")
            
            for pair_name, pair_data in data['forex_pairs'].items():
                output_lines.append(f"Pair: {pair_name}")
                if 'high' in pair_data:
                    output_lines.append(f"High: {pair_data['high']}")
                if 'average' in pair_data:
                    output_lines.append(f"Average: {pair_data['average']}")
                if 'low' in pair_data:
                    output_lines.append(f"Low: {pair_data['low']}")
                if 'mt4_action' in pair_data:
                    output_lines.append(f"MT4 Action: {pair_data['mt4_action']}")
                if 'exit' in pair_data:
                    output_lines.append(f"Exit: {pair_data['exit']}")
                output_lines.append("")
        
        if data.get('premium_swing_trades'):
            output_lines.append("PREMIUM SWING TRADES")
            output_lines.append("")
            output_lines.append("Monday - Wednesday")
            output_lines.append("")
            
            for trade in data['premium_swing_trades']:
                if 'ticker' in trade and 'company_name' in trade:
                    output_lines.append(f"{trade['ticker']} – {trade['company_name']}")
                    output_lines.append("")
                
                if trade.get('earnings_date'):
                    output_lines.append(f"    EARNINGS DATE: {trade['earnings_date']}")
                
                if trade.get('analysis'):
                    analysis_text = ' '.join(trade['analysis'])
                    output_lines.append(f"    ANALYSIS: {analysis_text}")
                
                if trade.get('strategy'):
                    output_lines.append(f"    STRATEGY: {trade['strategy']}")
                
                output_lines.append("")
        
        if data.get('equities_options'):
            output_lines.append("EQUITIES AND OPTIONS")
            output_lines.append("")
            
            for option in data['equities_options']:
                output_lines.append(f"Symbol: {option['symbol']}")
                if '52_week_high' in option:
                    output_lines.append(f"52 Week High: {option['52_week_high']}")
                if '52_week_low' in option:
                    output_lines.append(f"52 Week Low: {option['52_week_low']}")
                output_lines.append("Strike Price:")
                output_lines.append("")
                
                if 'call_strike' in option:
                    output_lines.append(f"CALL > {option['call_strike']}")
                output_lines.append("")
                
                if 'put_strike' in option:
                    output_lines.append(f"PUT < {option['put_strike']}")
                
                if 'status' in option:
                    output_lines.append(f"Status: {option['status']}")
                
                output_lines.append("")
        
        return '\n'.join(output_lines)

async def test_fixed_scraper():
    """Test the fixed scraper"""
    try:
        scraper = FixedMyMamaScraper()
        logger.info("Testing fixed MyMama scraper...")
        
        # Get real alerts
        data = await scraper.get_real_alerts()
        
        if data['has_real_data']:
            logger.info("✅ Successfully extracted real data!")
            
            # Format output
            formatted_output = scraper.format_output(data)
            
            # Save formatted output
            output_file = scraper.output_dir / f'formatted_output_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
            with open(output_file, 'w') as f:
                f.write(formatted_output)
            
            logger.info(f"Formatted output saved to: {output_file}")
            
            # Print sample
            print("\n" + "="*50)
            print("SAMPLE FORMATTED OUTPUT:")
            print("="*50)
            print(formatted_output[:1000] + "..." if len(formatted_output) > 1000 else formatted_output)
            
            return True
        else:
            logger.warning("No real data available")
            return False
            
    except Exception as e:
        logger.error(f"Error testing scraper: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_fixed_scraper())