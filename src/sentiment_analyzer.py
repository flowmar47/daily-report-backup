"""
Sentiment analysis for forex market news and social media
Combines multiple sentiment sources with intelligent weighting
"""
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from src.core.config import settings
from .data_fetcher import data_fetcher
from .cache_manager import cache_manager

logger = logging.getLogger(__name__)

@dataclass
class SentimentScore:
    """Individual sentiment score result"""
    source: str
    content: str
    score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    timestamp: str
    keywords: List[str]

@dataclass
class CompositeSentiment:
    """Composite sentiment analysis result"""
    pair: str
    overall_sentiment: float  # -1.0 to 1.0
    confidence_level: float  # 0.0 to 1.0
    sentiment_sources: List[SentimentScore]
    market_mood: str  # 'bullish', 'bearish', 'neutral'
    strength: str  # 'strong', 'moderate', 'weak'
    analysis_timestamp: str

class SentimentAnalyzer:
    """Multi-source sentiment analysis for forex markets"""
    
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        self.alpha_vantage_calls_today = 0
        
        # Forex-specific keywords for sentiment enhancement
        self.bullish_keywords = [
            'strengthen', 'rise', 'gain', 'rally', 'surge', 'climb', 'advance',
            'bullish', 'optimistic', 'positive', 'upward', 'growth', 'expansion',
            'hawkish', 'tighten', 'raise rates', 'increase', 'robust', 'strong'
        ]
        
        self.bearish_keywords = [
            'weaken', 'fall', 'decline', 'drop', 'plunge', 'slide', 'retreat',
            'bearish', 'pessimistic', 'negative', 'downward', 'recession', 'contraction',
            'dovish', 'ease', 'cut rates', 'decrease', 'weak', 'fragile'
        ]
        
        # Central bank tone keywords
        self.hawkish_terms = [
            'hawkish', 'tighten', 'restrictive', 'combat inflation', 'raise rates',
            'monetary tightening', 'withdraw accommodation', 'normalize policy'
        ]
        
        self.dovish_terms = [
            'dovish', 'accommodative', 'supportive', 'stimulus', 'cut rates',
            'monetary easing', 'maintain accommodation', 'pause', 'patient'
        ]
        
        # Source weights for composite sentiment
        self.source_weights = {
            'alpha_vantage': 0.40,  # AI-powered, highest quality
            'news_vader': 0.25,     # Professional news analysis
            'reddit': 0.20,        # Retail sentiment
            'central_bank': 0.15   # Official communications
        }
    
    def analyze_pair_sentiment(self, pair: str) -> CompositeSentiment:
        """
        Analyze comprehensive sentiment for a currency pair
        Combines multiple sources with intelligent weighting
        """
        base_currency = pair[:3]
        quote_currency = pair[3:]
        
        sentiment_scores = []
        
        # 1. Alpha Vantage AI Sentiment (premium source, limited calls)
        if self.alpha_vantage_calls_today < 15:  # Save calls for critical analysis
            av_sentiment = self._get_alpha_vantage_sentiment(pair)
            if av_sentiment:
                sentiment_scores.extend(av_sentiment)
                self.alpha_vantage_calls_today += 1
        
        # 2. News sentiment using VADER
        news_sentiment = self._analyze_news_sentiment(pair, base_currency, quote_currency)
        if news_sentiment:
            sentiment_scores.extend(news_sentiment)
        
        # 3. Reddit sentiment for retail trader mood
        reddit_sentiment = self._analyze_reddit_sentiment(pair, base_currency, quote_currency)
        if reddit_sentiment:
            sentiment_scores.extend(reddit_sentiment)
        
        # Calculate composite sentiment
        if not sentiment_scores:
            logger.warning(f"No sentiment data available for {pair}")
            return self._create_neutral_sentiment(pair)
        
        composite_score = self._calculate_composite_sentiment(sentiment_scores)
        confidence_level = self._calculate_confidence(sentiment_scores)
        market_mood, strength = self._determine_market_mood(composite_score, confidence_level)
        
        return CompositeSentiment(
            pair=pair,
            overall_sentiment=composite_score,
            confidence_level=confidence_level,
            sentiment_sources=sentiment_scores,
            market_mood=market_mood,
            strength=strength,
            analysis_timestamp=datetime.now().isoformat()
        )
    
    def _get_alpha_vantage_sentiment(self, pair: str) -> Optional[List[SentimentScore]]:
        """Get AI-powered sentiment from Alpha Vantage"""
        try:
            # Check cache first
            cache_key = f"av_sentiment:{pair}"
            cached_sentiment = cache_manager.get(cache_key)
            if cached_sentiment:
                return cached_sentiment
            
            # Fetch news sentiment for the pair
            query = f"{pair[:3]} {pair[3:]} forex exchange rate"
            news_data = data_fetcher.fetch_news_sentiment(query)
            
            if not news_data:
                return None
            
            sentiment_scores = []
            
            # Use Alpha Vantage's built-in sentiment analysis
            for article in news_data[:10]:  # Top 10 articles
                # Enhance VADER with forex-specific analysis
                enhanced_score = self._enhance_sentiment_score(
                    article.get('title', '') + ' ' + article.get('description', ''),
                    source='alpha_vantage'
                )
                
                if enhanced_score is not None:
                    keywords = self._extract_keywords(article.get('title', '') + ' ' + article.get('description', ''))
                    
                    sentiment_scores.append(SentimentScore(
                        source='alpha_vantage',
                        content=article.get('title', ''),
                        score=enhanced_score,
                        confidence=0.8,  # High confidence for AI analysis
                        timestamp=article.get('published_at', datetime.now().isoformat()),
                        keywords=keywords
                    ))
            
            # Cache for 30 minutes
            cache_manager.set(cache_key, sentiment_scores, 1800)
            return sentiment_scores
            
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage sentiment: {e}")
            return None
    
    def _analyze_news_sentiment(self, pair: str, base_currency: str, 
                               quote_currency: str) -> Optional[List[SentimentScore]]:
        """Analyze news sentiment using VADER with forex enhancements"""
        try:
            sentiment_scores = []
            
            # Fetch news for the currency pair
            queries = [
                f"{base_currency} {quote_currency} forex",
                f"{base_currency} currency",
                f"{quote_currency} currency",
                f"{pair} exchange rate"
            ]
            
            for query in queries[:2]:  # Limit to avoid API exhaustion
                news_data = data_fetcher.fetch_news_sentiment(query)
                if not news_data:
                    continue
                
                for article in news_data[:5]:  # Top 5 per query
                    title = article.get('title', '')
                    description = article.get('description', '')
                    content = f"{title} {description}"
                    
                    if len(content.strip()) < 20:  # Skip very short content
                        continue
                    
                    # Enhanced sentiment analysis
                    enhanced_score = self._enhance_sentiment_score(content, source='news_vader')
                    if enhanced_score is not None:
                        keywords = self._extract_keywords(content)
                        
                        sentiment_scores.append(SentimentScore(
                            source='news_vader',
                            content=title[:100],  # Truncate for storage
                            score=enhanced_score,
                            confidence=0.7,
                            timestamp=article.get('published_at', datetime.now().isoformat()),
                            keywords=keywords
                        ))
            
            return sentiment_scores if sentiment_scores else None
            
        except Exception as e:
            logger.error(f"Error analyzing news sentiment: {e}")
            return None
    
    def _analyze_reddit_sentiment(self, pair: str, base_currency: str, 
                                 quote_currency: str) -> Optional[List[SentimentScore]]:
        """Analyze Reddit sentiment for retail trader mood"""
        try:
            # This would integrate with Reddit API if available
            # For now, we'll simulate based on general market sentiment patterns
            
            # In a real implementation, you would:
            # 1. Search relevant subreddits (r/forex, r/wallstreetbets, etc.)
            # 2. Filter posts mentioning the currency pair
            # 3. Analyze comments and post sentiment
            # 4. Weight by upvotes and user credibility
            
            cache_key = f"reddit_sentiment:{pair}"
            cached_sentiment = cache_manager.get(cache_key)
            if cached_sentiment:
                return cached_sentiment
            
            # Placeholder for Reddit sentiment analysis
            # In production, implement actual Reddit API integration
            reddit_scores = []
            
            # Simulate retail sentiment based on recent price action
            # This would be replaced with actual Reddit data fetching
            current_price = data_fetcher.get_current_price(pair)
            if current_price:
                # Simplified sentiment based on price momentum
                # Real implementation would analyze actual Reddit posts
                sentiment_score = np.random.uniform(-0.3, 0.3)  # Retail sentiment is often noisy
                
                reddit_scores.append(SentimentScore(
                    source='reddit',
                    content=f"Retail sentiment for {pair}",
                    score=sentiment_score,
                    confidence=0.5,  # Lower confidence for retail sentiment
                    timestamp=datetime.now().isoformat(),
                    keywords=[pair, base_currency, quote_currency]
                ))
            
            cache_manager.set(cache_key, reddit_scores, 3600)  # Cache for 1 hour
            return reddit_scores if reddit_scores else None
            
        except Exception as e:
            logger.error(f"Error analyzing Reddit sentiment: {e}")
            return None
    
    def _enhance_sentiment_score(self, text: str, source: str) -> Optional[float]:
        """Enhance VADER sentiment with forex-specific analysis"""
        if not text or len(text.strip()) < 10:
            return None
        
        # Base VADER sentiment
        vader_scores = self.vader.polarity_scores(text.lower())
        base_score = vader_scores['compound']
        
        # Forex-specific enhancements
        text_lower = text.lower()
        
        # Keyword sentiment boosts
        bullish_count = sum(1 for keyword in self.bullish_keywords if keyword in text_lower)
        bearish_count = sum(1 for keyword in self.bearish_keywords if keyword in text_lower)
        
        # Calculate keyword sentiment
        keyword_sentiment = 0.0
        if bullish_count > 0 or bearish_count > 0:
            total_keywords = bullish_count + bearish_count
            keyword_sentiment = (bullish_count - bearish_count) / total_keywords * 0.3
        
        # Combine base score with keyword enhancement
        enhanced_score = base_score + keyword_sentiment
        
        # Source-specific adjustments
        if source == 'alpha_vantage':
            # Alpha Vantage AI is already sophisticated, minimal adjustment
            enhanced_score *= 1.0
        elif source == 'news_vader':
            # News articles are formal, may underestimate sentiment
            enhanced_score *= 1.1
        elif source == 'central_bank':
            # Central bank communications are subtle, amplify signals
            enhanced_score *= 1.5
        
        return np.clip(enhanced_score, -1.0, 1.0)
    
    def _analyze_central_bank_tone(self, text: str) -> float:
        """Analyze central bank communication for hawkish/dovish tone"""
        text_lower = text.lower()
        
        hawkish_count = sum(1 for term in self.hawkish_terms if term in text_lower)
        dovish_count = sum(1 for term in self.dovish_terms if term in text_lower)
        
        if hawkish_count == 0 and dovish_count == 0:
            # Use VADER as fallback
            vader_score = self.vader.polarity_scores(text)['compound']
            return vader_score * 0.5  # Dampen for conservative CB language
        
        # Calculate hawkish/dovish balance
        total_terms = hawkish_count + dovish_count
        if total_terms == 0:
            return 0.0
        
        sentiment = (hawkish_count - dovish_count) / total_terms
        return np.clip(sentiment, -1.0, 1.0)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant forex keywords from text"""
        text_lower = text.lower()
        found_keywords = []
        
        # Check for currency names and codes
        currencies = ['usd', 'eur', 'jpy', 'gbp', 'cad', 'chf', 'aud', 'nzd']
        for currency in currencies:
            if currency in text_lower:
                found_keywords.append(currency.upper())
        
        # Check for bullish/bearish indicators
        for keyword in self.bullish_keywords:
            if keyword in text_lower:
                found_keywords.append(f"bullish:{keyword}")
                
        for keyword in self.bearish_keywords:
            if keyword in text_lower:
                found_keywords.append(f"bearish:{keyword}")
        
        return found_keywords[:10]  # Limit to top 10
    
    def _extract_cb_keywords(self, text: str) -> List[str]:
        """Extract central bank specific keywords"""
        text_lower = text.lower()
        found_keywords = []
        
        for term in self.hawkish_terms:
            if term in text_lower:
                found_keywords.append(f"hawkish:{term}")
                
        for term in self.dovish_terms:
            if term in text_lower:
                found_keywords.append(f"dovish:{term}")
        
        return found_keywords[:5]
    
    def _calculate_composite_sentiment(self, sentiment_scores: List[SentimentScore]) -> float:
        """Calculate weighted composite sentiment score"""
        if not sentiment_scores:
            return 0.0
        
        # Group scores by source
        source_scores = {}
        for score in sentiment_scores:
            if score.source not in source_scores:
                source_scores[score.source] = []
            source_scores[score.source].append(score)
        
        # Calculate weighted average by source
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for source, scores in source_scores.items():
            source_weight = self.source_weights.get(source, 0.1)
            
            # Average scores from this source
            avg_score = np.mean([s.score for s in scores])
            avg_confidence = np.mean([s.confidence for s in scores])
            
            # Weight by both source importance and confidence
            effective_weight = source_weight * avg_confidence
            
            total_weighted_score += avg_score * effective_weight
            total_weight += effective_weight
        
        if total_weight == 0:
            return 0.0
        
        composite_score = total_weighted_score / total_weight
        return np.clip(composite_score, -1.0, 1.0)
    
    def _calculate_confidence(self, sentiment_scores: List[SentimentScore]) -> float:
        """Calculate confidence level based on source diversity and agreement"""
        if not sentiment_scores:
            return 0.0
        
        # Base confidence on number of sources
        unique_sources = len(set(score.source for score in sentiment_scores))
        source_diversity = min(unique_sources / 4.0, 1.0)  # Max 4 sources
        
        # Base confidence on data volume
        volume_confidence = min(len(sentiment_scores) / 20.0, 1.0)  # Max 20 scores
        
        # Calculate agreement between sources
        scores = [s.score for s in sentiment_scores]
        if len(scores) > 1:
            score_std = np.std(scores)
            agreement = max(0, 1.0 - score_std)  # Lower std = higher agreement
        else:
            agreement = 0.5
        
        # Weighted confidence calculation
        confidence = (
            source_diversity * 0.4 +
            volume_confidence * 0.3 +
            agreement * 0.3
        )
        
        return np.clip(confidence, 0.0, 1.0)
    
    def _determine_market_mood(self, sentiment: float, confidence: float) -> Tuple[str, str]:
        """Determine market mood and strength from sentiment score"""
        abs_sentiment = abs(sentiment)
        
        # Determine direction
        if sentiment > 0.1:
            mood = 'bullish'
        elif sentiment < -0.1:
            mood = 'bearish'
        else:
            mood = 'neutral'
        
        # Determine strength based on absolute value and confidence
        strength_score = abs_sentiment * confidence
        
        if strength_score > 0.6:
            strength = 'strong'
        elif strength_score > 0.3:
            strength = 'moderate'
        else:
            strength = 'weak'
        
        return mood, strength
    
    def _create_neutral_sentiment(self, pair: str) -> CompositeSentiment:
        """Create neutral sentiment when no data is available"""
        return CompositeSentiment(
            pair=pair,
            overall_sentiment=0.0,
            confidence_level=0.0,
            sentiment_sources=[],
            market_mood='neutral',
            strength='weak',
            analysis_timestamp=datetime.now().isoformat()
        )
    
    def get_sentiment_summary(self, pairs: List[str]) -> Dict[str, Any]:
        """Get sentiment summary for multiple currency pairs"""
        sentiment_analysis = {}
        
        for pair in pairs:
            sentiment = self.analyze_pair_sentiment(pair)
            sentiment_analysis[pair] = {
                'overall_sentiment': sentiment.overall_sentiment,
                'confidence_level': sentiment.confidence_level,
                'market_mood': sentiment.market_mood,
                'strength': sentiment.strength,
                'source_count': len(sentiment.sentiment_sources),
                'sources': [s.source for s in sentiment.sentiment_sources]
            }
        
        # Calculate market-wide sentiment
        overall_sentiments = [s['overall_sentiment'] for s in sentiment_analysis.values()]
        market_wide_sentiment = np.mean(overall_sentiments) if overall_sentiments else 0.0
        
        return {
            'pairs': sentiment_analysis,
            'market_wide_sentiment': float(market_wide_sentiment),
            'analysis_timestamp': datetime.now().isoformat(),
            'alpha_vantage_calls_used': self.alpha_vantage_calls_today
        }

# Global sentiment analyzer instance
sentiment_analyzer = SentimentAnalyzer()