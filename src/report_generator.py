"""
Professional trading signal report generation
Formats signals for MT4 compatibility with clear risk management
"""
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import os

from .signal_generator import TradingSignal, SignalComponent
from src.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class SignalReport:
    """Complete signal report structure"""
    report_id: str
    generation_timestamp: str
    signals: Dict[str, TradingSignal]
    market_overview: Dict[str, Any]
    risk_disclaimer: str
    expiry_timestamp: str

class ReportGenerator:
    """Professional trading signal report generator"""
    
    def __init__(self):
        self.risk_disclaimer = self._get_risk_disclaimer()
        self.decimal_precision = {
            'EURUSD': 5,
            'GBPUSD': 5,
            'USDCAD': 5,
            'USDCHF': 5,
            'USDJPY': 3,
            'CHFJPY': 3,
            'EURJPY': 3,
            'GBPJPY': 3
        }
    
    def generate_comprehensive_report(self, signals: Dict[str, TradingSignal], 
                                    output_format: str = 'txt') -> str:
        """
        Generate comprehensive trading signal report
        
        Args:
            signals: Dictionary of currency pair signals
            output_format: 'txt', 'json', 'html', or 'csv'
        
        Returns:
            Formatted report string
        """
        try:
            logger.info(f"Generating {output_format} report for {len(signals)} signals")
            
            # Create market overview
            market_overview = self._create_market_overview(signals)
            
            # Generate report ID
            report_id = self._generate_report_id()
            
            # Create report structure
            report = SignalReport(
                report_id=report_id,
                generation_timestamp=datetime.now().isoformat(),
                signals=signals,
                market_overview=market_overview,
                risk_disclaimer=self.risk_disclaimer,
                expiry_timestamp=self._get_next_friday().isoformat()
            )
            
            # Format based on requested output
            if output_format.lower() == 'txt':
                return self._format_text_report(report)
            elif output_format.lower() == 'json':
                return self._format_json_report(report)
            elif output_format.lower() == 'html':
                return self._format_html_report(report)
            elif output_format.lower() == 'csv':
                return self._format_csv_report(report)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
                
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return self._create_error_report(str(e))
    
    def _format_text_report(self, report: SignalReport) -> str:
        """Format report as professional text output for MT4 compatibility"""
        lines = []
        
        # Header
        lines.extend([
            "=" * 80,
            f"FOREX TRADING SIGNALS REPORT",
            f"Report ID: {report.report_id}",
            f"Generated: {self._format_datetime(report.generation_timestamp)}",
            f"Valid Until: {self._format_datetime(report.expiry_timestamp)}",
            "=" * 80,
            ""
        ])
        
        # Market Overview
        lines.extend([
            "MARKET OVERVIEW",
            "-" * 40,
            f"Total Pairs Analyzed: {report.market_overview['total_pairs']}",
            f"Active Signals: {report.market_overview['active_signals']}",
            f"Hold Recommendations: {report.market_overview['hold_signals']}",
            f"Average Confidence: {report.market_overview['avg_confidence']:.1%}",
            f"Market Sentiment: {report.market_overview['market_sentiment'].title()}",
            ""
        ])
        
        # Individual Signals
        lines.append("TRADING SIGNALS")
        lines.append("=" * 80)
        
        # Sort signals by confidence (highest first)
        sorted_signals = sorted(
            report.signals.items(),
            key=lambda x: x[1].confidence,
            reverse=True
        )
        
        for pair, signal in sorted_signals:
            lines.extend(self._format_signal_text(pair, signal))
            lines.append("")
        
        # Analysis Summary
        lines.extend([
            "ANALYSIS SUMMARY",
            "=" * 80,
            ""
        ])
        
        for pair, signal in sorted_signals:
            if signal.action != 'HOLD':
                lines.extend([
                    f"{pair}: {signal.action} Signal",
                    f"  Entry: {self._format_price(pair, signal.entry_price)}",
                    f"  Target: {self._format_price(pair, signal.exit_price)} ({signal.target_pips:.0f} pips)",
                    f"  Stop Loss: {self._format_price(pair, signal.stop_loss)}",
                    f"  Confidence: {signal.confidence:.1%}",
                    f"  Achievement Probability: {signal.weekly_achievement_probability:.1%}",
                    ""
                ])
        
        # Risk Management
        lines.extend([
            "RISK MANAGEMENT GUIDELINES",
            "=" * 80,
            "• Position Size: Risk maximum 1-2% of account per trade",
            "• Stop Loss: Always use provided stop loss levels",
            "• Take Profit: Target levels based on Average Weekly Range",
            "• Time Frame: Signals valid until Friday 23:59 GMT",
            "• Review: Monitor economic calendar for high-impact events",
            ""
        ])
        
        # Component Analysis Legend
        lines.extend([
            "ANALYSIS COMPONENTS",
            "=" * 80,
            "Technical Analysis: 4H candlestick patterns + indicators (35% weight)",
            "Economic Fundamentals: Interest rates, GDP, inflation data (25% weight)",
            "Market Sentiment: News and AI-powered sentiment (20% weight)",
            "Geopolitical Events: GDELT event analysis (10% weight)",
            "4H Candlestick Patterns: Dedicated pattern analysis (10% weight)",
            ""
        ])
        
        # Footer
        lines.extend([
            "=" * 80,
            report.risk_disclaimer,
            "=" * 80
        ])
        
        return "\n".join(lines)
    
    def _format_signal_text(self, pair: str, signal: TradingSignal) -> List[str]:
        """Format individual signal for text output"""
        lines = []
        
        # Signal Header
        action_symbol = "📈" if signal.action == "BUY" else "📉" if signal.action == "SELL" else "⏸️"
        confidence_stars = "★" * int(signal.confidence * 5)
        
        lines.extend([
            f"{pair} - {signal.action} {action_symbol}",
            f"Confidence: {signal.confidence:.1%} {confidence_stars}",
            f"Signal Strength: {signal.signal_strength:+.2f}",
            "-" * 40
        ])
        
        if signal.action != 'HOLD':
            # Trading Details
            lines.extend([
                "TRADING DETAILS:",
                f"  Entry Price:     {self._format_price(pair, signal.entry_price)}",
                f"  Exit Target:     {self._format_price(pair, signal.exit_price)}",
                f"  Stop Loss:       {self._format_price(pair, signal.stop_loss)}",
                f"  Target Pips:     {signal.target_pips:.0f} pips",
                f"  Days to Target:  {signal.days_to_target} days",
                ""
            ])
            
            # Add signal category and timeframe information if available
            technical_component = signal.components.get('technical')
            if technical_component and hasattr(technical_component, 'details'):
                signal_category = technical_component.details.get('signal_category', 'Standard')
                expected_timeframe = technical_component.details.get('expected_timeframe', 'Variable')
                lines.extend([
                    "SIGNAL ANALYSIS:",
                    f"  Signal Category: {signal_category}",
                    f"  Expected Time:   {expected_timeframe}",
                    f"  Strength Level:  {abs(signal.signal_strength):.3f}",
                    ""
                ])
        else:
            # Hold reasoning
            technical_component = signal.components.get('technical')
            if technical_component and hasattr(technical_component, 'details'):
                reason = technical_component.details.get('reason', 'Insufficient signal strength')
            else:
                reason = 'Insufficient signal strength'
            
            lines.extend([
                "HOLD RECOMMENDATION:",
                f"  Reason: {reason}",
                f"  Current signal too weak for reliable entry",
                ""
            ])
        
        # Component Breakdown
        lines.append("ANALYSIS BREAKDOWN:")
        
        for component_name, component in signal.components.items():
            if isinstance(component, SignalComponent):
                score_indicator = self._get_score_indicator(component.score)
                lines.append(
                    f"  {component_name.title():12}: {component.score:+.2f} "
                    f"({component.confidence:.1%}) {score_indicator}"
                )
        
        return lines
    
    def _format_json_report(self, report: SignalReport) -> str:
        """Format report as JSON for API integration"""
        # Convert TradingSignal objects to dictionaries
        json_signals = {}
        for pair, signal in report.signals.items():
            signal_dict = asdict(signal)
            # Convert components to dictionaries
            if 'components' in signal_dict:
                components_dict = {}
                for comp_name, comp in signal_dict['components'].items():
                    if hasattr(comp, '__dict__'):
                        components_dict[comp_name] = asdict(comp)
                    else:
                        components_dict[comp_name] = comp
                signal_dict['components'] = components_dict
            json_signals[pair] = signal_dict
        
        report_dict = {
            'report_id': report.report_id,
            'generation_timestamp': report.generation_timestamp,
            'expiry_timestamp': report.expiry_timestamp,
            'market_overview': report.market_overview,
            'signals': json_signals,
            'risk_disclaimer': report.risk_disclaimer
        }
        
        return json.dumps(report_dict, indent=2, default=str)
    
    def _format_csv_report(self, report: SignalReport) -> str:
        """Format report as CSV for spreadsheet analysis"""
        lines = []
        
        # CSV Header
        headers = [
            'Pair', 'Action', 'Entry_Price', 'Exit_Price', 'Stop_Loss',
            'Target_Pips', 'Confidence', 'Signal_Strength', 'Days_to_Target',
            'Achievement_Probability', 'Technical_Score', 'Economic_Score',
            'Sentiment_Score', 'Geopolitical_Score', 'Analysis_Timestamp'
        ]
        lines.append(','.join(headers))
        
        # Signal data
        for pair, signal in report.signals.items():
            components = signal.components
            tech_score = components.get('technical').score if components.get('technical') else 0
            econ_score = components.get('economic').score if components.get('economic') else 0
            sent_score = components.get('sentiment').score if components.get('sentiment') else 0
            geo_score = components.get('geopolitical').score if components.get('geopolitical') else 0
            
            row = [
                pair,
                signal.action,
                signal.entry_price or '',
                signal.exit_price or '',
                signal.stop_loss or '',
                signal.target_pips or '',
                signal.confidence,
                signal.signal_strength,
                signal.days_to_target or '',
                signal.weekly_achievement_probability,
                tech_score,
                econ_score,
                sent_score,
                geo_score,
                signal.analysis_timestamp
            ]
            lines.append(','.join(str(x) for x in row))
        
        return '\n'.join(lines)
    
    def _format_html_report(self, report: SignalReport) -> str:
        """Format report as HTML for web display"""
        # Generate signals HTML first
        signals_html = ""
        for pair, signal in report.signals.items():
            signal_class = signal.action.lower()
            confidence_stars = "★" * int(signal.confidence * 5)
            
            signal_html = f"""
            <div class="signal {signal_class}">
                <h3>{pair} - {signal.action} (Confidence: {signal.confidence:.1%} {confidence_stars})</h3>
            """
            
            if signal.action != 'HOLD':
                signal_html += f"""
                <table>
                    <tr><td>Entry Price:</td><td>{self._format_price(pair, signal.entry_price)}</td></tr>
                    <tr><td>Exit Target:</td><td>{self._format_price(pair, signal.exit_price)}</td></tr>
                    <tr><td>Stop Loss:</td><td>{self._format_price(pair, signal.stop_loss)}</td></tr>
                    <tr><td>Target Pips:</td><td>{signal.target_pips:.0f}</td></tr>
                    <tr><td>Achievement Probability:</td><td>{signal.weekly_achievement_probability:.1%}</td></tr>
                </table>
                """
            
            # Components
            signal_html += '<div class="components"><h4>Analysis Components:</h4><ul>'
            for comp_name, component in signal.components.items():
                if hasattr(component, 'score') and hasattr(component, 'confidence'):
                    signal_html += f"<li>{comp_name.title()}: {component.score:+.2f} ({component.confidence:.1%})</li>"
            signal_html += '</ul></div></div>'
            
            signals_html += signal_html
        
        # Now create the template with all variables available
        html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>Forex Trading Signals Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .overview {{ background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .signal {{ border: 1px solid #bdc3c7; margin: 15px 0; padding: 15px; border-radius: 5px; }}
        .buy {{ border-left: 5px solid #27ae60; }}
        .sell {{ border-left: 5px solid #e74c3c; }}
        .hold {{ border-left: 5px solid #f39c12; }}
        .components {{ background: #f8f9fa; padding: 10px; margin: 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        .disclaimer {{ background: #fff3cd; padding: 15px; margin: 20px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Forex Trading Signals Report</h1>
        <p>Report ID: {report.report_id}</p>
        <p>Generated: {self._format_datetime(report.generation_timestamp)}</p>
        <p>Valid Until: {self._format_datetime(report.expiry_timestamp)}</p>
    </div>
    
    <div class="overview">
        <h2>Market Overview</h2>
        <table>
            <tr><td>Total Pairs Analyzed:</td><td>{report.market_overview['total_pairs']}</td></tr>
            <tr><td>Active Signals:</td><td>{report.market_overview['active_signals']}</td></tr>
            <tr><td>Hold Recommendations:</td><td>{report.market_overview['hold_signals']}</td></tr>
            <tr><td>Average Confidence:</td><td>{report.market_overview['avg_confidence']:.1%}</td></tr>
            <tr><td>Market Sentiment:</td><td>{report.market_overview['market_sentiment'].title()}</td></tr>
        </table>
    </div>
    
    <h2>Trading Signals</h2>
    {signals_html}
    
    <div class="disclaimer">
        <h3>Risk Disclaimer</h3>
        <p>{report.risk_disclaimer}</p>
    </div>
</body>
</html>"""
        
        return html_template
    
    def save_report(self, report_content: str, output_format: str, 
                   output_dir: str = "reports") -> str:
        """Save report to file and return file path"""
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"forex_signals_{timestamp}.{output_format}"
            filepath = os.path.join(output_dir, filename)
            
            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Report saved to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            raise
    
    def _create_market_overview(self, signals: Dict[str, TradingSignal]) -> Dict[str, Any]:
        """Create market overview statistics"""
        total_pairs = len(signals)
        active_signals = sum(1 for s in signals.values() if s.action != 'HOLD')
        hold_signals = total_pairs - active_signals
        
        # Calculate average confidence
        confidences = [s.confidence for s in signals.values()]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Determine overall market sentiment
        signal_strengths = [s.signal_strength for s in signals.values()]
        avg_strength = sum(signal_strengths) / len(signal_strengths) if signal_strengths else 0.0
        
        if avg_strength > 0.2:
            market_sentiment = 'bullish'
        elif avg_strength < -0.2:
            market_sentiment = 'bearish'
        else:
            market_sentiment = 'neutral'
        
        return {
            'total_pairs': total_pairs,
            'active_signals': active_signals,
            'hold_signals': hold_signals,
            'avg_confidence': avg_confidence,
            'avg_signal_strength': avg_strength,
            'market_sentiment': market_sentiment
        }
    
    def _format_price(self, pair: str, price: Optional[float]) -> str:
        """Format price with appropriate decimal places"""
        if price is None:
            return "N/A"
        
        precision = self.decimal_precision.get(pair, 5)
        decimal_price = Decimal(str(price)).quantize(
            Decimal('0.' + '0' * precision), 
            rounding=ROUND_HALF_UP
        )
        return str(decimal_price)
    
    def _format_datetime(self, iso_string: str) -> str:
        """Format ISO datetime string for display"""
        try:
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            return iso_string
    
    def _get_score_indicator(self, score: float) -> str:
        """Get visual indicator for score"""
        if score > 0.3:
            return "📈 Strong"
        elif score > 0.1:
            return "📊 Moderate"
        elif score > -0.1:
            return "➡️ Neutral"
        elif score > -0.3:
            return "📉 Weak"
        else:
            return "📉 Very Weak"
    
    def _get_pip_value(self, pair: str) -> float:
        """Get pip value for currency pair"""
        pip_values = {
            # Major Pairs (USD base/quote)
            'EURUSD': 0.0001, 'GBPUSD': 0.0001, 'USDJPY': 0.01, 'USDCHF': 0.0001,
            'AUDUSD': 0.0001, 'USDCAD': 0.0001, 'NZDUSD': 0.0001,
            # Cross Pairs (EUR base)
            'EURGBP': 0.0001, 'EURJPY': 0.01, 'EURCHF': 0.0001, 'EURAUD': 0.0001,
            'EURCAD': 0.0001, 'EURNZD': 0.0001,
            # Cross Pairs (GBP base)
            'GBPJPY': 0.01, 'GBPCHF': 0.0001, 'GBPAUD': 0.0001, 'GBPCAD': 0.0001,
            'GBPNZD': 0.0001,
            # Cross Pairs (JPY quote)
            'CHFJPY': 0.01, 'AUDJPY': 0.01, 'CADJPY': 0.01, 'NZDJPY': 0.01,
            # Other Cross Pairs
            'AUDCHF': 0.0001, 'AUDCAD': 0.0001, 'AUDNZD': 0.0001, 'CADCHF': 0.0001,
            'NZDCHF': 0.0001, 'NZDCAD': 0.0001
        }
        return pip_values.get(pair, 0.0001)
    
    def _generate_report_id(self) -> str:
        """Generate unique report ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:17]  # Include microseconds
        return f"FSR_{timestamp}"
    
    def _get_next_friday(self) -> datetime:
        """Get next Friday for signal expiry"""
        today = datetime.now()
        days_ahead = 4 - today.weekday()  # Friday is 4
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return today + timedelta(days=days_ahead)
    
    def _get_risk_disclaimer(self) -> str:
        """Get standard risk disclaimer"""
        return """
RISK DISCLAIMER: Trading foreign exchange carries a high level of risk and may not be 
suitable for all investors. The high degree of leverage can work against you as well as 
for you. Before deciding to trade foreign exchange you should carefully consider your 
investment objectives, level of experience, and risk appetite. The possibility exists 
that you could sustain a loss of some or all of your initial investment. Only trade 
with money you can afford to lose. This analysis is for educational purposes only and 
should not be considered as financial advice. Past performance is not indicative of 
future results.
        """.strip()
    
    def _create_error_report(self, error_msg: str) -> str:
        """Create error report when generation fails"""
        return f"""
ERROR GENERATING FOREX SIGNALS REPORT
=====================================
Timestamp: {datetime.now().isoformat()}
Error: {error_msg}

Please contact system administrator for assistance.
        """.strip()

# Global report generator instance
report_generator = ReportGenerator()