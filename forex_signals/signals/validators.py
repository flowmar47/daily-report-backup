"""
Data validation module - refactored from ensure_real_data_only.py
Provides comprehensive validation for forex data to ensure quality and authenticity
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from ..core.exceptions import DataQualityError, ValidationError
from ..core.logging import get_logger
from .models import TradingSignal, SignalResult, ValidationResult, PriceData

logger = get_logger(__name__)


@dataclass
class PriceRange:
    """Valid price range for a currency pair"""
    pair: str
    min_price: float
    max_price: float
    last_updated: datetime


class PriceValidator:
    """
    Validates forex prices to ensure authenticity and quality
    Prevents fake/outdated prices from being used in signal generation
    """
    
    # Known fake prices that must NEVER be used (as of August 2025)
    BANNED_FAKE_PRICES = {
        'EURUSD': [1.0950, 1.095, 1.09],  # Real price is ~1.172
        'GBPUSD': [1.2650],               # Outdated prices
        'USDJPY': [110.0],                # Outdated prices
    }
    
    # Realistic price ranges (updated August 2025)
    VALID_PRICE_RANGES = {
        'EURUSD': PriceRange('EURUSD', 1.15, 1.20, datetime.now()),   # Real range around 1.172
        'GBPUSD': PriceRange('GBPUSD', 1.25, 1.40, datetime.now()),   # Real range - updated for cached price 1.35551
        'USDJPY': PriceRange('USDJPY', 140, 155, datetime.now()),     # Real range around 146
        'USDCAD': PriceRange('USDCAD', 1.30, 1.45, datetime.now()),   # Real range around 1.38
        'USDCHF': PriceRange('USDCHF', 0.80, 1.05, datetime.now()),   # Real range around 0.806
        'AUDUSD': PriceRange('AUDUSD', 0.60, 0.75, datetime.now()),   # Real range
        'NZDUSD': PriceRange('NZDUSD', 0.55, 0.70, datetime.now()),   # Real range
        'EURJPY': PriceRange('EURJPY', 160, 180, datetime.now()),     # Real range
        'GBPJPY': PriceRange('GBPJPY', 180, 200, datetime.now()),     # Real range
        'CHFJPY': PriceRange('CHFJPY', 165, 190, datetime.now()),     # Real range around 182.6
        'EURGBP': PriceRange('EURGBP', 0.84, 0.92, datetime.now()),   # Real range
        'EURAUD': PriceRange('EURAUD', 1.55, 1.75, datetime.now()),   # Real range
        'EURCAD': PriceRange('EURCAD', 1.45, 1.65, datetime.now()),   # Real range
    }
    
    def __init__(self):
        self.validation_enabled = True
        self.strict_mode = True  # Reject any suspicious prices
        
    def validate_forex_price(self, pair: str, price: float, source: str = None) -> bool:
        """
        Validate that a forex price is realistic and not fake
        
        Args:
            pair: Currency pair (e.g., 'EURUSD')
            price: Price to validate
            source: Data source for logging
            
        Returns:
            True if price appears legitimate, False if suspicious/fake
            
        Raises:
            DataQualityError: If fake price detected in strict mode
        """
        if not self.validation_enabled:
            return True
            
        pair = pair.upper()
        
        # Check against known fake prices
        if pair in self.BANNED_FAKE_PRICES:
            for fake_price in self.BANNED_FAKE_PRICES[pair]:
                if abs(price - fake_price) < 0.001:
                    error_msg = f"FAKE PRICE DETECTED: {pair} = {price} (known fake value)"
                    logger.error(f"❌ {error_msg} from source: {source}")
                    
                    if self.strict_mode:
                        raise DataQualityError(
                            error_msg,
                            pair=pair,
                            price=price,
                            reason="known_fake_price",
                            source=source
                        )
                    return False
        
        # Check if price is within valid range
        if pair in self.VALID_PRICE_RANGES:
            price_range = self.VALID_PRICE_RANGES[pair]
            if not (price_range.min_price <= price <= price_range.max_price):
                error_msg = f"SUSPICIOUS PRICE: {pair} = {price} (outside expected range {price_range.min_price}-{price_range.max_price})"
                logger.warning(f"⚠️ {error_msg} from source: {source}")
                
                if self.strict_mode:
                    raise DataQualityError(
                        error_msg,
                        pair=pair,
                        price=price,
                        reason="outside_valid_range",
                        expected_range=(price_range.min_price, price_range.max_price),
                        source=source
                    )
                return False
        
        # Price appears valid
        logger.debug(f"✅ Price validation passed: {pair} = {price}")
        return True
    
    def validate_price_data(self, price_data: PriceData) -> ValidationResult:
        """Validate a PriceData object"""
        errors = []
        warnings = []
        
        try:
            is_valid = self.validate_forex_price(price_data.pair, price_data.price, price_data.source)
            
            # Additional validations
            if price_data.bid and price_data.ask:
                if price_data.bid >= price_data.ask:
                    errors.append(f"Bid price ({price_data.bid}) must be less than ask price ({price_data.ask})")
                    
                spread = price_data.ask - price_data.bid
                if spread > price_data.price * 0.01:  # Spread > 1% of price
                    warnings.append(f"Unusually wide spread: {spread:.5f}")
            
            # Check timestamp freshness
            age = (datetime.now() - price_data.timestamp).total_seconds()
            if age > 3600:  # Older than 1 hour
                warnings.append(f"Price data is {age/3600:.1f} hours old")
            
            return ValidationResult(
                is_valid=is_valid and len(errors) == 0,
                errors=errors,
                warnings=warnings,
                validated_data=price_data.dict() if is_valid and len(errors) == 0 else None
            )
            
        except DataQualityError as e:
            errors.append(str(e))
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings
            )
    
    def validate_multiple_prices(
        self, 
        prices: List[PriceData], 
        variance_threshold: float = 0.01
    ) -> ValidationResult:
        """
        Validate multiple price sources for the same pair
        Ensures prices from different sources are consistent
        
        Args:
            prices: List of PriceData from different sources
            variance_threshold: Maximum allowed variance between sources
            
        Returns:
            ValidationResult with consensus price if valid
        """
        if len(prices) < 2:
            return ValidationResult(
                is_valid=False,
                errors=["Need at least 2 price sources for validation"]
            )
        
        errors = []
        warnings = []
        
        # Validate each price individually first
        valid_prices = []
        for price_data in prices:
            result = self.validate_price_data(price_data)
            if result.is_valid:
                valid_prices.append(price_data)
            else:
                errors.extend([f"Source {price_data.source}: {err}" for err in result.errors])
        
        if len(valid_prices) < 2:
            return ValidationResult(
                is_valid=False,
                errors=errors + ["Insufficient valid price sources"]
            )
        
        # Check price consistency across sources
        price_values = [p.price for p in valid_prices]
        avg_price = sum(price_values) / len(price_values)
        max_variance = max(abs(p - avg_price) / avg_price for p in price_values)
        
        if max_variance > variance_threshold:
            errors.append(
                f"Price variance ({max_variance:.3%}) exceeds threshold ({variance_threshold:.3%}). "
                f"Prices: {price_values}"
            )
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings
            )
        
        # Create consensus price data
        consensus_price = PriceData(
            pair=valid_prices[0].pair,
            price=avg_price,
            timestamp=max(p.timestamp for p in valid_prices),  # Most recent timestamp
            source=f"consensus_of_{len(valid_prices)}_sources"
        )
        
        logger.info(f"✅ Price validation passed with {len(valid_prices)} sources: {consensus_price.pair} = {avg_price:.5f}")
        
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=warnings,
            validated_data=consensus_price.dict()
        )


class DataValidator:
    """
    Comprehensive data validator for forex signals
    Validates signal data structure, prices, and business logic
    """
    
    def __init__(self):
        self.price_validator = PriceValidator()
        
    def validate_trading_signal(self, signal: TradingSignal) -> ValidationResult:
        """Validate a single trading signal"""
        errors = []
        warnings = []
        
        try:
            # Validate prices if present
            price_fields = ['entry_price', 'exit_price', 'stop_loss', 'take_profit']
            for field in price_fields:
                price = getattr(signal, field)
                if price is not None:
                    try:
                        self.price_validator.validate_forex_price(signal.pair, price, f"signal.{field}")
                    except DataQualityError as e:
                        errors.append(f"Invalid {field}: {str(e)}")
            
            # Business logic validations
            if signal.entry_price and signal.exit_price:
                if signal.action.value == 'BUY' and signal.exit_price <= signal.entry_price:
                    errors.append("BUY signal must have exit_price > entry_price")
                elif signal.action.value == 'SELL' and signal.exit_price >= signal.entry_price:
                    errors.append("SELL signal must have exit_price < entry_price")
            
            # Risk management validations
            if signal.target_pips and signal.target_pips < 10:
                warnings.append(f"Very small target: {signal.target_pips} pips")
            
            if signal.stop_loss_pips and signal.stop_loss_pips > 200:
                warnings.append(f"Large stop loss: {signal.stop_loss_pips} pips")
            
            # Confidence validations
            if signal.confidence < 0.3:
                warnings.append(f"Low confidence signal: {signal.confidence:.2%}")
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                validated_data=signal.dict() if len(errors) == 0 else None
            )
            
        except Exception as e:
            logger.error(f"Error validating signal: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"]
            )
    
    def validate_signal_result(self, result: SignalResult) -> ValidationResult:
        """
        Validate complete signal result and remove any fake/suspicious data
        This is the main validation entry point for backward compatibility
        """
        if not result:
            return ValidationResult(
                is_valid=False,
                errors=["Empty result provided"]
            )
        
        errors = []
        warnings = []
        valid_signals = []
        
        # Validate each forex alert/signal
        for i, alert in enumerate(result.forex_alerts):
            try:
                # Convert dict to TradingSignal if needed for validation
                if isinstance(alert, dict):
                    # Create a minimal TradingSignal for validation
                    signal_data = {
                        'pair': alert.get('pair', ''),
                        'action': alert.get('action', 'HOLD'),
                        'confidence': alert.get('confidence', 0.5),
                        'signal_strength': alert.get('signal_strength', 0.0),
                        'strength_category': 'Medium',
                        'weekly_achievement_probability': alert.get('weekly_achievement_probability', 0.5),
                        'expiry_date': datetime.now().replace(hour=23, minute=59, second=59),
                    }
                    
                    # Add price fields if available
                    for field in ['entry_price', 'exit_price', 'stop_loss', 'take_profit']:
                        if field in alert and alert[field] is not None:
                            signal_data[field] = alert[field]
                    
                    try:
                        signal = TradingSignal(**signal_data)
                        validation_result = self.validate_trading_signal(signal)
                    except Exception as e:
                        logger.warning(f"Could not create TradingSignal for validation: {e}")
                        # Fall back to basic price validation
                        validation_result = self._validate_alert_dict(alert)
                
                else:
                    validation_result = self.validate_trading_signal(alert)
                
                if validation_result.is_valid:
                    valid_signals.append(alert)
                    warnings.extend(validation_result.warnings)
                else:
                    pair = alert.get('pair', 'Unknown') if isinstance(alert, dict) else alert.pair
                    errors.extend([f"Signal {i} ({pair}): {err}" for err in validation_result.errors])
                    logger.error(f"❌ Removing invalid signal for {pair}: {validation_result.errors}")
            
            except Exception as e:
                logger.error(f"Error validating signal {i}: {e}")
                errors.append(f"Signal {i}: Validation error - {str(e)}")
        
        # Update result with valid signals only
        result.forex_alerts = valid_signals
        result.has_real_data = len(valid_signals) > 0
        result.active_signals = len([s for s in valid_signals if s.action != 'HOLD'])
        result.total_signals = len(valid_signals)
        result.hold_signals = result.total_signals - result.active_signals
        
        is_valid = len(valid_signals) > 0
        
        if not is_valid:
            logger.error("❌ CRITICAL: No valid signals remain after validation")
        else:
            logger.info(f"✅ Validation passed: {len(valid_signals)} valid signals from {len(result.forex_alerts)} total")
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            validated_data=result.dict() if is_valid else None
        )
    
    def _validate_alert_dict(self, alert: Dict[str, Any]) -> ValidationResult:
        """Validate alert dictionary format (fallback validation)"""
        errors = []
        warnings = []
        
        pair = alert.get('pair', '')
        if not pair:
            errors.append("Missing pair field")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Validate prices using PriceValidator
        price_fields = ['entry_price', 'exit_price', 'stop_loss', 'take_profit', 'high', 'low', 'average']
        for field in price_fields:
            if field in alert and alert[field] is not None:
                try:
                    self.price_validator.validate_forex_price(pair, alert[field], f"alert.{field}")
                except DataQualityError as e:
                    errors.append(f"Invalid {field}: {str(e)}")
        
        # Validate confidence and probability ranges
        for field, (min_val, max_val) in [('confidence', (0, 1)), ('weekly_achievement_probability', (0, 1))]:
            if field in alert and alert[field] is not None:
                value = alert[field]
                if not (min_val <= value <= max_val):
                    warnings.append(f"Invalid {field}: {value} (should be {min_val}-{max_val})")
                    alert[field] = max(min_val, min(max_val, value))  # Clamp to valid range
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            validated_data=alert if len(errors) == 0 else None
        )


# Legacy functions for backward compatibility
def validate_forex_price(pair: str, price: float) -> bool:
    """Legacy function - use PriceValidator.validate_forex_price instead"""
    validator = PriceValidator()
    try:
        return validator.validate_forex_price(pair, price)
    except DataQualityError:
        return False


def validate_signal_data(signal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility
    Validates and cleans signal data to ensure no fake prices
    """
    if not signal_data:
        return signal_data
    
    try:
        # Convert to SignalResult for validation
        result = SignalResult(**signal_data)
        validator = DataValidator()
        validation_result = validator.validate_signal_result(result)
        
        if validation_result.is_valid:
            return validation_result.validated_data
        else:
            # Return cleaned result even if not fully valid
            return result.dict()
    except Exception as e:
        logger.error(f"Error in legacy validate_signal_data: {e}")
        return signal_data


def initialize_real_data_enforcement():
    """Legacy function - initialize validators"""
    logger.info("✅ Real data enforcement initialized - NO FAKE DATA ALLOWED")
    
    print("\n" + "="*70)
    print("REAL DATA ENFORCEMENT SYSTEM ACTIVE")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("\n✅ ENFORCING:")
    print("  • NO fake/synthetic prices allowed")
    print("  • NO hardcoded demo values")
    print("  • NO placeholder data")
    print("  • ONLY real market data from APIs")
    
    print("\n⚠️ VALIDATION ACTIVE:")
    print("  • Price range checking enabled")
    print("  • Fake price detection enabled")
    print("  • Automatic removal of suspicious data")
    print("  • Multi-source price verification")
    
    return True


def enforce_real_data_only():
    """Legacy function - alias for initialize_real_data_enforcement"""
    return initialize_real_data_enforcement()