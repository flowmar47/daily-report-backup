"""
Unit tests for sentiment analysis functionality
Tests use mock data structures that match real API responses
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sentiment_analyzer import (
    SentimentAnalyzer, SentimentScore, CompositeSentiment, sentiment_analyzer
)

class TestSentimentAnalyzer:
    """Test sentiment analysis functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.analyzer = SentimentAnalyzer()
    
    def test_initialization(self):
        """Test SentimentAnalyzer initialization"""
        assert self.analyzer.vader is not None
        assert self.analyzer.alpha_vantage_calls_today == 0
        assert len(self.analyzer.bullish_keywords) > 0
        assert len(self.analyzer.bearish_keywords) > 0
        assert len(self.analyzer.hawkish_terms) > 0
        assert len(self.analyzer.dovish_terms) > 0
        assert len(self.analyzer.source_weights) > 0
    
    def test_enhance_sentiment_score_bullish(self):
        """Test sentiment enhancement with bullish content"""
        bullish_text = "USD strengthens significantly as economic growth surges and rates rise"
        
        score = self.analyzer._enhance_sentiment_score(bullish_text, 'news_vader')
        
        assert score is not None
        assert score > 0  # Should be positive for bullish content
        assert -1.0 <= score <= 1.0
    
    def test_enhance_sentiment_score_bearish(self):
        """Test sentiment enhancement with bearish content"""
        bearish_text = "Currency weakens dramatically as recession fears mount and rates fall"
        
        score = self.analyzer._enhance_sentiment_score(bearish_text, 'news_vader')
        
        assert score is not None
        assert score < 0  # Should be negative for bearish content
        assert -1.0 <= score <= 1.0
    
    def test_enhance_sentiment_score_empty_text(self):
        """Test sentiment enhancement with empty text"""
        score = self.analyzer._enhance_sentiment_score("", 'news_vader')
        assert score is None
        
        score_short = self.analyzer._enhance_sentiment_score("hi", 'news_vader')
        assert score_short is None
    
    def test_analyze_central_bank_tone_hawkish(self):
        """Test central bank tone analysis for hawkish content"""
        hawkish_text = "The central bank will tighten monetary policy to combat inflation by raising rates"
        
        tone = self.analyzer._analyze_central_bank_tone(hawkish_text)
        
        assert tone > 0  # Should be positive for hawkish tone
        assert -1.0 <= tone <= 1.0
    
    def test_analyze_central_bank_tone_dovish(self):
        """Test central bank tone analysis for dovish content"""
        dovish_text = "The bank will maintain accommodative policy and cut rates to support growth"
        
        tone = self.analyzer._analyze_central_bank_tone(dovish_text)
        
        assert tone < 0  # Should be negative for dovish tone
        assert -1.0 <= tone <= 1.0
    
    def test_analyze_central_bank_tone_neutral(self):
        """Test central bank tone analysis for neutral content"""
        neutral_text = "The bank will review economic conditions at the next meeting"
        
        tone = self.analyzer._analyze_central_bank_tone(neutral_text)
        
        assert -1.0 <= tone <= 1.0  # Should be within bounds
    
    def test_extract_keywords(self):
        """Test keyword extraction from text"""
        text = "USD strengthens against EUR as bullish sentiment rises with rate increases"
        
        keywords = self.analyzer._extract_keywords(text)
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert 'USD' in keywords
        assert 'EUR' in keywords
        assert any('bullish:' in kw for kw in keywords)
    
    def test_extract_cb_keywords(self):
        """Test central bank keyword extraction"""
        text = "The Fed adopts a hawkish stance to tighten monetary policy amid inflation"
        
        keywords = self.analyzer._extract_cb_keywords(text)
        
        assert isinstance(keywords, list)
        assert any('hawkish:' in kw for kw in keywords)
    
    def test_calculate_composite_sentiment(self):
        """Test composite sentiment calculation"""
        sentiment_scores = [
            SentimentScore(
                source='alpha_vantage',
                content='Bullish news',
                score=0.8,
                confidence=0.9,
                timestamp='2024-01-01T00:00:00',
                keywords=['bullish']
            ),
            SentimentScore(
                source='news_vader',
                content='Positive outlook',
                score=0.6,
                confidence=0.7,
                timestamp='2024-01-01T00:00:00',
                keywords=['positive']
            ),
            SentimentScore(
                source='reddit',
                content='Bearish sentiment',
                score=-0.4,
                confidence=0.5,
                timestamp='2024-01-01T00:00:00',
                keywords=['bearish']
            )
        ]
        
        composite = self.analyzer._calculate_composite_sentiment(sentiment_scores)
        
        assert -1.0 <= composite <= 1.0
        assert composite > 0  # Should be positive overall (alpha_vantage has highest weight)
    
    def test_calculate_composite_sentiment_empty(self):
        """Test composite sentiment with empty scores"""
        composite = self.analyzer._calculate_composite_sentiment([])
        assert composite == 0.0
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        # High confidence scenario
        high_conf_scores = [
            SentimentScore('alpha_vantage', 'content1', 0.8, 0.9, '2024-01-01', []),
            SentimentScore('news_vader', 'content2', 0.7, 0.8, '2024-01-01', []),
            SentimentScore('reddit', 'content3', 0.6, 0.7, '2024-01-01', []),
            SentimentScore('central_bank', 'content4', 0.5, 0.9, '2024-01-01', [])
        ]
        
        high_confidence = self.analyzer._calculate_confidence(high_conf_scores)
        assert 0.0 <= high_confidence <= 1.0
        assert high_confidence > 0.5  # Should be high with diverse sources
        
        # Low confidence scenario
        low_conf_scores = [
            SentimentScore('reddit', 'content1', 0.1, 0.3, '2024-01-01', [])
        ]
        
        low_confidence = self.analyzer._calculate_confidence(low_conf_scores)
        assert 0.0 <= low_confidence <= 1.0
        assert low_confidence < 0.5  # Should be low with single weak source
    
    def test_determine_market_mood(self):
        """Test market mood determination"""
        # Strong bullish (sentiment=0.8, confidence=0.9, strength_score=0.72 > 0.6)
        mood, strength = self.analyzer._determine_market_mood(0.8, 0.9)
        assert mood == 'bullish'
        assert strength == 'strong'
        
        # Weak bearish (sentiment=-0.4, confidence=0.7, strength_score=0.28 < 0.3)
        mood, strength = self.analyzer._determine_market_mood(-0.4, 0.7)
        assert mood == 'bearish'
        assert strength == 'weak'
        
        # Weak neutral
        mood, strength = self.analyzer._determine_market_mood(0.05, 0.3)
        assert mood == 'neutral'
        assert strength == 'weak'
    
    def test_create_neutral_sentiment(self):
        """Test neutral sentiment creation"""
        neutral = self.analyzer._create_neutral_sentiment('EURUSD')
        
        assert neutral.pair == 'EURUSD'
        assert neutral.overall_sentiment == 0.0
        assert neutral.confidence_level == 0.0
        assert neutral.market_mood == 'neutral'
        assert neutral.strength == 'weak'
        assert len(neutral.sentiment_sources) == 0
    
    @patch('src.sentiment_analyzer.data_fetcher')
    def test_analyze_news_sentiment(self, mock_data_fetcher):
        """Test news sentiment analysis"""
        mock_news_data = [
            {
                'title': 'USD strengthens significantly against EUR',
                'description': 'Strong economic data boosts dollar outlook',
                'published_at': '2024-01-01T00:00:00Z'
            },
            {
                'title': 'European economy shows weakness',
                'description': 'GDP falls as recession fears mount',
                'published_at': '2024-01-01T01:00:00Z'
            }
        ]
        
        mock_data_fetcher.fetch_news_sentiment.return_value = mock_news_data
        
        result = self.analyzer._analyze_news_sentiment('EURUSD', 'EUR', 'USD')
        
        assert result is not None
        assert len(result) > 0
        assert all(isinstance(score, SentimentScore) for score in result)
        assert all(score.source == 'news_vader' for score in result)
    
    @patch('src.sentiment_analyzer.data_fetcher')
    def test_analyze_news_sentiment_no_data(self, mock_data_fetcher):
        """Test news sentiment analysis with no data"""
        mock_data_fetcher.fetch_news_sentiment.return_value = None
        
        result = self.analyzer._analyze_news_sentiment('EURUSD', 'EUR', 'USD')
        
        assert result is None
    
    @patch('src.sentiment_analyzer.data_fetcher')
    def test_analyze_central_bank_sentiment(self, mock_data_fetcher):
        """Test central bank sentiment analysis"""
        mock_cb_feeds = [
            {
                'title': 'Fed announces hawkish policy stance',
                'summary': 'Central bank will tighten monetary policy to combat inflation',
                'published': '2024-01-01T00:00:00Z'
            }
        ]
        
        mock_data_fetcher.fetch_central_bank_feeds.return_value = mock_cb_feeds
        
        result = self.analyzer._analyze_central_bank_sentiment('USD', 'EUR')
        
        assert result is not None
        assert len(result) > 0
        assert all(isinstance(score, SentimentScore) for score in result)
        assert all(score.source == 'central_bank' for score in result)
    
    @patch('src.sentiment_analyzer.data_fetcher')
    @patch('src.sentiment_analyzer.cache_manager')
    def test_analyze_pair_sentiment_comprehensive(self, mock_cache, mock_data_fetcher):
        """Test comprehensive pair sentiment analysis"""
        # Mock cache misses
        mock_cache.get.return_value = None
        
        # Mock news data
        mock_data_fetcher.fetch_news_sentiment.return_value = [
            {
                'title': 'USD shows strength in forex markets',
                'description': 'Bullish sentiment drives currency higher',
                'published_at': '2024-01-01T00:00:00Z'
            }
        ]
        
        # Mock current price
        mock_data_fetcher.get_current_price.return_value = 1.1050
        
        # Mock central bank feeds
        mock_data_fetcher.fetch_central_bank_feeds.return_value = [
            {
                'title': 'Fed maintains hawkish stance',
                'summary': 'Monetary policy will remain restrictive',
                'published': '2024-01-01T00:00:00Z'
            }
        ]
        
        result = self.analyzer.analyze_pair_sentiment('EURUSD')
        
        assert isinstance(result, CompositeSentiment)
        assert result.pair == 'EURUSD'
        assert -1.0 <= result.overall_sentiment <= 1.0
        assert 0.0 <= result.confidence_level <= 1.0
        assert result.market_mood in ['bullish', 'bearish', 'neutral']
        assert result.strength in ['strong', 'moderate', 'weak']
        assert len(result.sentiment_sources) >= 0
    
    @patch('src.sentiment_analyzer.data_fetcher')
    def test_get_sentiment_summary(self, mock_data_fetcher):
        """Test sentiment summary for multiple pairs"""
        # Mock all data fetcher methods to return None (neutral scenario)
        mock_data_fetcher.fetch_news_sentiment.return_value = None
        mock_data_fetcher.get_current_price.return_value = None
        mock_data_fetcher.fetch_central_bank_feeds.return_value = None
        
        pairs = ['EURUSD', 'GBPUSD']
        result = self.analyzer.get_sentiment_summary(pairs)
        
        assert 'pairs' in result
        assert 'market_wide_sentiment' in result
        assert 'analysis_timestamp' in result
        assert 'alpha_vantage_calls_used' in result
        
        assert len(result['pairs']) == len(pairs)
        for pair in pairs:
            assert pair in result['pairs']
            pair_data = result['pairs'][pair]
            assert 'overall_sentiment' in pair_data
            assert 'confidence_level' in pair_data
            assert 'market_mood' in pair_data
            assert 'strength' in pair_data

class TestSentimentScore:
    """Test SentimentScore dataclass"""
    
    def test_sentiment_score_creation(self):
        """Test creating a sentiment score"""
        score = SentimentScore(
            source='news_vader',
            content='Test content',
            score=0.5,
            confidence=0.8,
            timestamp='2024-01-01T00:00:00',
            keywords=['test', 'bullish']
        )
        
        assert score.source == 'news_vader'
        assert score.content == 'Test content'
        assert score.score == 0.5
        assert score.confidence == 0.8
        assert score.timestamp == '2024-01-01T00:00:00'
        assert score.keywords == ['test', 'bullish']

class TestCompositeSentiment:
    """Test CompositeSentiment dataclass"""
    
    def test_composite_sentiment_creation(self):
        """Test creating a composite sentiment"""
        sentiment_score = SentimentScore(
            source='news_vader',
            content='Test content',
            score=0.5,
            confidence=0.8,
            timestamp='2024-01-01T00:00:00',
            keywords=['test']
        )
        
        composite = CompositeSentiment(
            pair='EURUSD',
            overall_sentiment=0.3,
            confidence_level=0.7,
            sentiment_sources=[sentiment_score],
            market_mood='bullish',
            strength='moderate',
            analysis_timestamp='2024-01-01T00:00:00'
        )
        
        assert composite.pair == 'EURUSD'
        assert composite.overall_sentiment == 0.3
        assert composite.confidence_level == 0.7
        assert len(composite.sentiment_sources) == 1
        assert composite.market_mood == 'bullish'
        assert composite.strength == 'moderate'

class TestGlobalSentimentAnalyzer:
    """Test global sentiment analyzer instance"""
    
    def test_global_instance_exists(self):
        """Test that global sentiment analyzer instance exists"""
        assert sentiment_analyzer is not None
        assert isinstance(sentiment_analyzer, SentimentAnalyzer)
    
    def test_global_instance_has_vader(self):
        """Test global instance has VADER analyzer"""
        assert sentiment_analyzer.vader is not None
    
    def test_global_instance_has_keywords(self):
        """Test global instance has keyword lists"""
        assert len(sentiment_analyzer.bullish_keywords) > 0
        assert len(sentiment_analyzer.bearish_keywords) > 0
        assert len(sentiment_analyzer.hawkish_terms) > 0
        assert len(sentiment_analyzer.dovish_terms) > 0

class TestIntegration:
    """Integration tests for sentiment analysis"""
    
    def test_sentiment_enhancement_consistency(self):
        """Test that sentiment enhancement is consistent"""
        analyzer = SentimentAnalyzer()
        
        # Same text should produce same score
        text = "USD strengthens significantly against major currencies"
        score1 = analyzer._enhance_sentiment_score(text, 'news_vader')
        score2 = analyzer._enhance_sentiment_score(text, 'news_vader')
        
        assert score1 == score2
    
    def test_source_weight_normalization(self):
        """Test that source weights are properly normalized"""
        analyzer = SentimentAnalyzer()
        
        # All weights should be positive and sum to reasonable total
        weights = list(analyzer.source_weights.values())
        assert all(w > 0 for w in weights)
        assert 0.8 <= sum(weights) <= 1.2  # Should be close to 1.0
    
    def test_keyword_detection_robustness(self):
        """Test keyword detection with various text formats"""
        analyzer = SentimentAnalyzer()
        
        test_cases = [
            "USD/EUR strengthens",
            "usd eur currency pair",
            "DOLLAR gains against EURO",
            "bullish outlook for usd"
        ]
        
        for text in test_cases:
            keywords = analyzer._extract_keywords(text)
            assert isinstance(keywords, list)
            # Should detect at least one currency or sentiment keyword
            has_currency = any(kw in ['USD', 'EUR'] for kw in keywords)
            has_sentiment = any('bullish:' in kw or 'bearish:' in kw for kw in keywords)
            assert has_currency or has_sentiment
    
    def test_confidence_calculation_edge_cases(self):
        """Test confidence calculation with edge cases"""
        analyzer = SentimentAnalyzer()
        
        # Empty list
        conf_empty = analyzer._calculate_confidence([])
        assert conf_empty == 0.0
        
        # Single score
        single_score = [SentimentScore('test', 'content', 0.5, 0.8, '2024-01-01', [])]
        conf_single = analyzer._calculate_confidence(single_score)
        assert 0.0 <= conf_single <= 1.0
        
        # Highly disagreeing scores
        disagreeing_scores = [
            SentimentScore('source1', 'content1', 0.9, 0.9, '2024-01-01', []),
            SentimentScore('source2', 'content2', -0.9, 0.9, '2024-01-01', [])
        ]
        conf_disagreeing = analyzer._calculate_confidence(disagreeing_scores)
        assert 0.0 <= conf_disagreeing <= 1.0
    
    def test_market_mood_boundary_conditions(self):
        """Test market mood determination at boundary conditions"""
        analyzer = SentimentAnalyzer()
        
        # Test exact boundaries (sentiment > 0.1 for bullish)
        mood, strength = analyzer._determine_market_mood(0.11, 0.5)
        assert mood == 'bullish'
        
        mood, strength = analyzer._determine_market_mood(-0.11, 0.5)
        assert mood == 'bearish'
        
        mood, strength = analyzer._determine_market_mood(0.0, 0.5)
        assert mood == 'neutral'
        
        # Test boundary at exactly 0.1 (should be neutral)
        mood, strength = analyzer._determine_market_mood(0.1, 0.5)
        assert mood == 'neutral'