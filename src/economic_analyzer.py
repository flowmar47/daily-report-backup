"""
Economic analysis for currency fundamental strength assessment
Processes FRED data, economic indicators, and calendar events
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

from src.core.config import settings
from .data_fetcher import data_fetcher

logger = logging.getLogger(__name__)

@dataclass
class EconomicIndicatorScore:
    """Economic indicator scoring result"""
    indicator: str
    current_value: float
    previous_value: Optional[float]
    change_percent: Optional[float]
    score: float  # -1.0 to 1.0 (negative = worse, positive = better)
    impact_weight: float
    last_updated: str

@dataclass
class CurrencyStrength:
    """Currency strength assessment"""
    currency: str
    overall_score: float  # -1.0 to 1.0
    indicator_scores: List[EconomicIndicatorScore]
    interest_rate: Optional[float]
    gdp_growth: Optional[float]
    inflation_rate: Optional[float]
    unemployment_rate: Optional[float]
    confidence_level: float

class EconomicAnalyzer:
    """Economic fundamental analysis for currency pairs"""
    
    def __init__(self):
        self.economic_indicators = {
            'USD': ['DFF', 'GDP', 'CPIAUCSL', 'UNRATE'],
            'EUR': ['ECBDFR', 'CLVMNACSCAB1GQEU19'],
            'JPY': ['JPNCPIALLMINMEI'],
            'GBP': [],
            'CAD': ['IRSTCB01CAM156N', 'CANCPIALLMINMEI'],
            'CHF': ['SZLTIR01CHM156N', 'CHECPIALLMINMEI'],
        }
        self.indicator_weights = {
            # Interest rate indicators (highest weight)
            'DFF': 0.30,  # Federal Funds Rate
            'ECBDFR': 0.30,  # ECB Deposit Rate
            'IRSTCB01CAM156N': 0.30,  # Canada Interest Rate
            'SZLTIR01CHM156N': 0.30,  # Swiss Interest Rate
            
            # GDP Growth (high weight)
            'GDP': 0.25,
            'CLVMNACSCAB1GQEU19': 0.25,  # EU GDP
            
            # Inflation (high weight)
            'CPIAUCSL': 0.25,  # US CPI
            'JPNCPIALLMINMEI': 0.25,  # Japan CPI
            'CANCPIALLMINMEI': 0.25,  # Canada CPI
            'CHECPIALLMINMEI': 0.25,  # Switzerland CPI
            
            # Unemployment (medium weight)
            'UNRATE': 0.20,  # US Unemployment
            
            # Trade/Exchange rates (lower weight)
            'DEXUSEU': 0.10,  # USD/EUR exchange rate
        }
        
        # Scoring factors for different indicators
        self.scoring_factors = {
            'interest_rate': {
                'direction': 1,  # Higher rates = stronger currency
                'volatility_threshold': 0.25  # 25 basis points
            },
            'gdp_growth': {
                'direction': 1,  # Higher growth = stronger currency
                'volatility_threshold': 0.5  # 0.5% change
            },
            'inflation': {
                'direction': -1,  # Higher inflation = weaker currency (above target)
                'target': 2.0,  # 2% inflation target
                'volatility_threshold': 0.3
            },
            'unemployment': {
                'direction': -1,  # Higher unemployment = weaker currency
                'volatility_threshold': 0.2  # 0.2% change
            }
        }
    
    def analyze_currency_strength(self, currency: str) -> Optional[CurrencyStrength]:
        """
        Analyze fundamental strength of a currency
        Uses real economic data from FRED API
        """
        if currency not in self.economic_indicators:
            logger.warning(f"No economic indicators configured for {currency}")
            return None
        
        indicators = self.economic_indicators[currency]
        indicator_scores = []
        
        # Fetch and analyze each economic indicator
        for indicator_id in indicators:
            score = self._analyze_indicator(indicator_id, currency)
            if score:
                indicator_scores.append(score)
        
        if not indicator_scores:
            logger.warning(f"No indicator data available for {currency}")
            return None
        
        # Calculate overall currency strength
        overall_score = self._calculate_overall_score(indicator_scores)
        confidence_level = self._calculate_confidence(indicator_scores)
        
        # Extract key economic metrics
        interest_rate = self._extract_interest_rate(indicator_scores)
        gdp_growth = self._extract_gdp_growth(indicator_scores)
        inflation_rate = self._extract_inflation_rate(indicator_scores)
        unemployment_rate = self._extract_unemployment_rate(indicator_scores)
        
        return CurrencyStrength(
            currency=currency,
            overall_score=overall_score,
            indicator_scores=indicator_scores,
            interest_rate=interest_rate,
            gdp_growth=gdp_growth,
            inflation_rate=inflation_rate,
            unemployment_rate=unemployment_rate,
            confidence_level=confidence_level
        )
    
    def _analyze_indicator(self, indicator_id: str, currency: str) -> Optional[EconomicIndicatorScore]:
        """Analyze a single economic indicator"""
        try:
            # Fetch data from FRED
            fred_data = data_fetcher.fetch_fred_data(indicator_id)
            if not fred_data or 'data' not in fred_data:
                logger.warning(f"No FRED data for indicator {indicator_id}")
                return None
            
            data_points = fred_data['data']
            if len(data_points) < 1:
                return None
            
            # Get current and previous values
            current_point = data_points[0]  # Most recent
            current_value = current_point['value']
            
            previous_value = None
            change_percent = None
            
            if len(data_points) > 1:
                previous_point = data_points[1]
                previous_value = previous_point['value']
                
                if previous_value != 0:
                    change_percent = ((current_value - previous_value) / previous_value) * 100
            
            # Calculate indicator score
            score = self._score_indicator(indicator_id, current_value, previous_value, change_percent)
            
            # Get impact weight
            impact_weight = self.indicator_weights.get(indicator_id, 0.1)
            
            return EconomicIndicatorScore(
                indicator=indicator_id,
                current_value=current_value,
                previous_value=previous_value,
                change_percent=change_percent,
                score=score,
                impact_weight=impact_weight,
                last_updated=current_point['date']
            )
            
        except Exception as e:
            logger.error(f"Error analyzing indicator {indicator_id}: {e}")
            return None
    
    def _score_indicator(self, indicator_id: str, current_value: float, 
                        previous_value: Optional[float], change_percent: Optional[float]) -> float:
        """Score an individual economic indicator"""
        
        # Determine indicator type and scoring method
        if any(rate_id in indicator_id.upper() for rate_id in ['DFF', 'ECBDFR', 'IRST']):
            return self._score_interest_rate(current_value, previous_value, change_percent)
        
        elif any(gdp_id in indicator_id.upper() for gdp_id in ['GDP', 'CLVMNA']):
            return self._score_gdp_growth(current_value, previous_value, change_percent)
        
        elif any(cpi_id in indicator_id.upper() for cpi_id in ['CPI', 'CPIAUCSL']):
            return self._score_inflation(current_value, previous_value, change_percent)
        
        elif 'UNRATE' in indicator_id.upper():
            return self._score_unemployment(current_value, previous_value, change_percent)
        
        else:
            # Generic scoring for other indicators
            return self._score_generic(current_value, previous_value, change_percent)
    
    def _score_interest_rate(self, current: float, previous: Optional[float], 
                           change_pct: Optional[float]) -> float:
        """Score interest rate indicators"""
        score = 0.0
        
        # Base score: higher rates = stronger currency
        if current >= 5.0:
            score += 0.8
        elif current >= 3.0:
            score += 0.5
        elif current >= 1.0:
            score += 0.2
        else:
            score -= 0.3  # Very low rates are negative
        
        # Change momentum
        if change_pct is not None:
            if change_pct > 0.1:  # Rising rates
                score += 0.3
            elif change_pct < -0.1:  # Falling rates
                score -= 0.3
        
        return np.clip(score, -1.0, 1.0)
    
    def _score_gdp_growth(self, current: float, previous: Optional[float], 
                         change_pct: Optional[float]) -> float:
        """Score GDP growth indicators"""
        score = 0.0
        
        # Base score: higher growth = stronger currency
        if current >= 3.0:
            score += 0.8
        elif current >= 2.0:
            score += 0.5
        elif current >= 1.0:
            score += 0.2
        elif current >= 0:
            score -= 0.1
        else:
            score -= 0.6  # Negative growth
        
        # Growth momentum
        if change_pct is not None:
            if change_pct > 0.5:  # Accelerating growth
                score += 0.2
            elif change_pct < -0.5:  # Decelerating growth
                score -= 0.2
        
        return np.clip(score, -1.0, 1.0)
    
    def _score_inflation(self, current: float, previous: Optional[float], 
                        change_pct: Optional[float]) -> float:
        """Score inflation indicators"""
        score = 0.0
        target = 2.0  # Most central banks target 2%
        
        # Distance from target
        distance = abs(current - target)
        
        if distance <= 0.5:  # Close to target
            score += 0.6
        elif distance <= 1.0:  # Moderately close
            score += 0.2
        elif distance <= 2.0:  # Somewhat far
            score -= 0.2
        else:  # Very far from target
            score -= 0.6
        
        # Trend direction
        if change_pct is not None:
            if current > target and change_pct > 0.2:  # Rising above target
                score -= 0.3
            elif current < target and change_pct < -0.2:  # Falling below target
                score -= 0.2
        
        return np.clip(score, -1.0, 1.0)
    
    def _score_unemployment(self, current: float, previous: Optional[float], 
                          change_pct: Optional[float]) -> float:
        """Score unemployment indicators"""
        score = 0.0
        
        # Base score: lower unemployment = stronger currency
        if current <= 3.5:
            score += 0.8
        elif current <= 5.0:
            score += 0.5
        elif current <= 7.0:
            score += 0.1
        elif current <= 10.0:
            score -= 0.3
        else:
            score -= 0.7
        
        # Change momentum
        if change_pct is not None:
            if change_pct < -0.1:  # Falling unemployment
                score += 0.2
            elif change_pct > 0.1:  # Rising unemployment
                score -= 0.2
        
        return np.clip(score, -1.0, 1.0)
    
    def _score_generic(self, current: float, previous: Optional[float], 
                      change_pct: Optional[float]) -> float:
        """Generic scoring for other indicators"""
        score = 0.0
        
        if change_pct is not None:
            if change_pct > 2.0:
                score += 0.3
            elif change_pct > 0:
                score += 0.1
            elif change_pct < -2.0:
                score -= 0.3
            else:
                score -= 0.1
        
        return np.clip(score, -1.0, 1.0)
    
    def _calculate_overall_score(self, indicator_scores: List[EconomicIndicatorScore]) -> float:
        """Calculate weighted overall currency strength score"""
        total_weighted_score = 0.0
        total_weights = 0.0
        
        for score in indicator_scores:
            total_weighted_score += score.score * score.impact_weight
            total_weights += score.impact_weight
        
        if total_weights == 0:
            return 0.0
        
        overall_score = total_weighted_score / total_weights
        return np.clip(overall_score, -1.0, 1.0)
    
    def _calculate_confidence(self, indicator_scores: List[EconomicIndicatorScore]) -> float:
        """Calculate confidence level based on data quality and consistency"""
        if not indicator_scores:
            return 0.0
        
        # Base confidence on number of indicators
        base_confidence = min(len(indicator_scores) / 5.0, 1.0)
        
        # Adjust for data freshness
        current_date = datetime.now()
        freshness_penalty = 0.0
        
        for score in indicator_scores:
            try:
                data_date = datetime.strptime(score.last_updated, '%Y-%m-%d')
                days_old = (current_date - data_date).days
                
                if days_old > 90:  # More than 3 months old
                    freshness_penalty += 0.1
                elif days_old > 30:  # More than 1 month old
                    freshness_penalty += 0.05
                    
            except ValueError:
                freshness_penalty += 0.1  # Unknown date format
        
        # Adjust for score consistency
        scores = [s.score for s in indicator_scores]
        score_std = np.std(scores) if len(scores) > 1 else 0.0
        consistency_bonus = max(0, (1.0 - score_std) * 0.2)
        
        final_confidence = base_confidence - freshness_penalty + consistency_bonus
        return np.clip(final_confidence, 0.0, 1.0)
    
    def _extract_interest_rate(self, scores: List[EconomicIndicatorScore]) -> Optional[float]:
        """Extract current interest rate from indicator scores"""
        for score in scores:
            if any(rate_id in score.indicator.upper() for rate_id in ['DFF', 'ECBDFR', 'IRST']):
                return score.current_value
        return None
    
    def _extract_gdp_growth(self, scores: List[EconomicIndicatorScore]) -> Optional[float]:
        """Extract GDP growth rate from indicator scores"""
        for score in scores:
            if any(gdp_id in score.indicator.upper() for gdp_id in ['GDP', 'CLVMNA']):
                return score.current_value
        return None
    
    def _extract_inflation_rate(self, scores: List[EconomicIndicatorScore]) -> Optional[float]:
        """Extract inflation rate from indicator scores"""
        for score in scores:
            if any(cpi_id in score.indicator.upper() for cpi_id in ['CPI', 'CPIAUCSL']):
                return score.current_value
        return None
    
    def _extract_unemployment_rate(self, scores: List[EconomicIndicatorScore]) -> Optional[float]:
        """Extract unemployment rate from indicator scores"""
        for score in scores:
            if 'UNRATE' in score.indicator.upper():
                return score.current_value
        return None
    
    def calculate_currency_differential(self, base_currency: str, 
                                      quote_currency: str) -> Dict[str, Any]:
        """
        Calculate economic strength differential between two currencies
        Returns comprehensive comparison for signal generation
        """
        # Analyze both currencies
        base_strength = self.analyze_currency_strength(base_currency)
        quote_strength = self.analyze_currency_strength(quote_currency)
        
        if not base_strength or not quote_strength:
            return {
                'error': f'Insufficient economic data for {base_currency}/{quote_currency}',
                'base_currency': base_currency,
                'quote_currency': quote_currency
            }
        
        # Calculate differentials
        overall_differential = base_strength.overall_score - quote_strength.overall_score
        
        # Interest rate differential (most important for forex)
        interest_rate_diff = None
        if base_strength.interest_rate is not None and quote_strength.interest_rate is not None:
            interest_rate_diff = base_strength.interest_rate - quote_strength.interest_rate
        
        # GDP growth differential
        gdp_diff = None
        if base_strength.gdp_growth is not None and quote_strength.gdp_growth is not None:
            gdp_diff = base_strength.gdp_growth - quote_strength.gdp_growth
        
        # Inflation differential
        inflation_diff = None
        if base_strength.inflation_rate is not None and quote_strength.inflation_rate is not None:
            inflation_diff = base_strength.inflation_rate - quote_strength.inflation_rate
        
        # Unemployment differential
        unemployment_diff = None
        if base_strength.unemployment_rate is not None and quote_strength.unemployment_rate is not None:
            unemployment_diff = quote_strength.unemployment_rate - base_strength.unemployment_rate  # Inverted
        
        # Overall signal strength
        signal_strength = self._calculate_signal_strength(
            overall_differential, interest_rate_diff, gdp_diff, inflation_diff, unemployment_diff
        )
        
        # Economic calendar impact
        calendar_impact = self._analyze_calendar_impact(base_currency, quote_currency)
        
        return {
            'pair': f"{base_currency}{quote_currency}",
            'base_currency': base_currency,
            'quote_currency': quote_currency,
            'overall_differential': float(overall_differential),
            'signal_strength': float(signal_strength),
            'differentials': {
                'interest_rate': float(interest_rate_diff) if interest_rate_diff is not None else None,
                'gdp_growth': float(gdp_diff) if gdp_diff is not None else None,
                'inflation': float(inflation_diff) if inflation_diff is not None else None,
                'unemployment': float(unemployment_diff) if unemployment_diff is not None else None
            },
            'base_strength': {
                'overall_score': base_strength.overall_score,
                'interest_rate': base_strength.interest_rate,
                'gdp_growth': base_strength.gdp_growth,
                'inflation_rate': base_strength.inflation_rate,
                'unemployment_rate': base_strength.unemployment_rate,
                'confidence': base_strength.confidence_level
            },
            'quote_strength': {
                'overall_score': quote_strength.overall_score,
                'interest_rate': quote_strength.interest_rate,
                'gdp_growth': quote_strength.gdp_growth,
                'inflation_rate': quote_strength.inflation_rate,
                'unemployment_rate': quote_strength.unemployment_rate,
                'confidence': quote_strength.confidence_level
            },
            'calendar_impact': calendar_impact,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _calculate_signal_strength(self, overall_diff: float, ir_diff: Optional[float],
                                 gdp_diff: Optional[float], inf_diff: Optional[float],
                                 unemp_diff: Optional[float]) -> float:
        """Calculate composite signal strength from differentials"""
        
        signal_components = []
        
        # Overall differential (base weight)
        signal_components.append((overall_diff, 0.4))
        
        # Interest rate differential (highest importance for forex)
        if ir_diff is not None:
            ir_signal = np.tanh(ir_diff * 2)  # Normalize large differences
            signal_components.append((ir_signal, 0.6))
        
        # GDP growth differential
        if gdp_diff is not None:
            gdp_signal = np.tanh(gdp_diff * 0.5)
            signal_components.append((gdp_signal, 0.3))
        
        # Inflation differential (moderate impact)
        if inf_diff is not None:
            inf_signal = np.tanh(-inf_diff * 0.3)  # Negative because higher inflation weakens currency
            signal_components.append((inf_signal, 0.2))
        
        # Unemployment differential
        if unemp_diff is not None:
            unemp_signal = np.tanh(unemp_diff * 0.4)
            signal_components.append((unemp_signal, 0.2))
        
        # Calculate weighted average
        if not signal_components:
            return 0.0
        
        total_weighted = sum(signal * weight for signal, weight in signal_components)
        total_weight = sum(weight for signal, weight in signal_components)
        
        final_signal = total_weighted / total_weight if total_weight > 0 else 0.0
        return np.clip(final_signal, -1.0, 1.0)
    
    def _analyze_calendar_impact(self, base_currency: str, quote_currency: str) -> Dict[str, Any]:
        """Analyze upcoming economic calendar events impact"""
        try:
            calendar_events = data_fetcher.fetch_finnhub_economic_calendar()
            if not calendar_events:
                return {'events': [], 'impact_score': 0.0}
            
            relevant_events = []
            impact_score = 0.0
            
            # Map currency to country codes
            currency_to_country = {
                'USD': 'US',
                'EUR': 'EU',
                'JPY': 'JP',
                'CAD': 'CA',
                'CHF': 'CH',
                'GBP': 'GB'
            }
            
            base_country = currency_to_country.get(base_currency)
            quote_country = currency_to_country.get(quote_currency)
            
            for event in calendar_events:
                event_country = event.get('country')
                
                if event_country in [base_country, quote_country]:
                    # Calculate impact based on event importance and currency
                    event_impact = 0.5 if event.get('impact') == 'high' else 0.2
                    
                    if event_country == base_country:
                        impact_score += event_impact
                    else:
                        impact_score -= event_impact
                    
                    relevant_events.append({
                        'date': event.get('date'),
                        'country': event_country,
                        'event': event.get('event'),
                        'impact': event.get('impact'),
                        'currency_effect': 'base' if event_country == base_country else 'quote'
                    })
            
            return {
                'events': relevant_events[:5],  # Top 5 most relevant
                'impact_score': np.clip(impact_score, -1.0, 1.0),
                'base_events_count': len([e for e in relevant_events if e['currency_effect'] == 'base']),
                'quote_events_count': len([e for e in relevant_events if e['currency_effect'] == 'quote'])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing calendar impact: {e}")
            return {'events': [], 'impact_score': 0.0}

# Global economic analyzer instance
economic_analyzer = EconomicAnalyzer()