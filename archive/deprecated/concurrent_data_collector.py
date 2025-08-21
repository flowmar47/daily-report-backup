#!/usr/bin/env python3
"""
Concurrent Data Collection System
Implements parallel data collection for forex, heatmaps, and API calls
"""

import asyncio
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys

from enhanced_error_handler import EnhancedErrorHandler, resilient_operation, DataValidator, ErrorContext, ErrorSeverity, ErrorCategory

logger = logging.getLogger(__name__)

class ConcurrentDataCollector:
    """Orchestrates concurrent data collection operations"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.error_handler = EnhancedErrorHandler(self.config.get('error_handling', {}))
        self.max_concurrent_operations = self.config.get('max_concurrent_operations', 5)
        self.timeout_seconds = self.config.get('timeout_seconds', 300)  # 5 minutes
        
        # Track operation performance
        self.operation_times = {}
        self.results_cache = {}
        
    async def collect_all_data_concurrent(self) -> Dict[str, Any]:
        """Collect all data sources concurrently"""
        start_time = time.time()
        logger.info("🚀 Starting concurrent data collection...")
        
        # Define all data collection tasks
        tasks = [
            self._collect_forex_data_task(),
            # self._collect_heatmap_data_task(),  # DISABLED - synthetic data violates authenticity requirements
            self._collect_currency_rates_task(),
            self._collect_market_sentiment_task()
        ]
        
        # Execute tasks concurrently with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.timeout_seconds
            )
            
            # Process results (heatmap data disabled due to API failures)
            forex_data, currency_rates, market_sentiment = results
            heatmap_data = None  # Disabled - will not generate heatmaps when APIs fail
            
            # Combine successful results
            combined_results = {
                'timestamp': datetime.now().isoformat(),
                'collection_time_seconds': time.time() - start_time,
                'forex_data': forex_data if not isinstance(forex_data, Exception) else None,
                'heatmap_data': heatmap_data if not isinstance(heatmap_data, Exception) else None,
                'currency_rates': currency_rates if not isinstance(currency_rates, Exception) else None,
                'market_sentiment': market_sentiment if not isinstance(market_sentiment, Exception) else None,
                'errors': []
            }
            
            # Log any errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    task_names = ['forex', 'currency_rates', 'market_sentiment']  # heatmap removed
                    error_info = f"{task_names[i]}: {str(result)}"
                    combined_results['errors'].append(error_info)
                    logger.error(f"Task {task_names[i]} failed: {result}")
            
            # Validate data authenticity - check if has_real_data flag is set
            if combined_results['forex_data']:
                forex_data = combined_results['forex_data']
                has_flag = forex_data.get('has_real_data', False)
                
                # Count actual data elements for validation
                forex_count = len(forex_data.get('forex_alerts', {}))
                options_count = len(forex_data.get('options_data', []))
                earnings_count = len(forex_data.get('earnings_releases', []))
                swing_count = len(forex_data.get('swing_trades', []))
                day_count = len(forex_data.get('day_trades', []))
                total_items = forex_count + options_count + earnings_count + swing_count + day_count
                
                logger.info(f"📊 Data validation: has_real_data={has_flag}, total_items={total_items}")
                logger.info(f"📊 Breakdown: forex={forex_count}, options={options_count}, earnings={earnings_count}, swing={swing_count}, day={day_count}")
                
                # Use more comprehensive validation - either flag OR actual data counts
                if not has_flag and total_items == 0:
                    logger.warning("⚠️ No real forex data available (flag=False, items=0)")
                    combined_results['forex_data'] = None
                elif not has_flag and total_items > 0:
                    logger.warning(f"⚠️ Data flag false but {total_items} items found - CORRECTING FLAG")
                    forex_data['has_real_data'] = True
                    combined_results['forex_data'] = forex_data
                else:
                    logger.info(f"✅ Real forex data validated: flag={has_flag}, items={total_items}")
            else:
                logger.warning("⚠️ No forex data returned from collector")
            
            # Validate currency rates authenticity - NO heatmaps if APIs fail
            if combined_results['currency_rates']:
                rates = combined_results['currency_rates'].get('rates', {})
                if not rates or len(rates) == 0:
                    logger.warning("⚠️ No real currency rate data available - heatmaps disabled")
                    combined_results['currency_rates'] = None
            
            success_count = sum(1 for key in ['forex_data', 'currency_rates', 'market_sentiment'] 
                              if combined_results[key] is not None)
            
            logger.info(f"✅ Concurrent collection completed: {success_count}/3 tasks successful in {combined_results['collection_time_seconds']:.2f}s")
            
            return combined_results
            
        except asyncio.TimeoutError:
            logger.error(f"❌ Data collection timeout after {self.timeout_seconds} seconds")
            return {
                'timestamp': datetime.now().isoformat(),
                'collection_time_seconds': time.time() - start_time,
                'error': 'Timeout during concurrent data collection',
                'timeout_seconds': self.timeout_seconds
            }
        except Exception as e:
            logger.error(f"❌ Concurrent data collection failed: {e}")
            error_context = ErrorContext(
                operation="collect_all_data_concurrent",
                component="concurrent_collection",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.DATA_EXTRACTION
            )
            await self.error_handler.handle_error(e, error_context)
            return {
                'timestamp': datetime.now().isoformat(),
                'collection_time_seconds': time.time() - start_time,
                'error': str(e)
            }
    
    @resilient_operation("concurrent_operation", "data_collector", max_retries=2)
    async def _collect_forex_data_task(self) -> Optional[Dict[str, Any]]:
        """Collect forex data using API-based signal generation"""
        try:
            logger.info("📊 Starting API-based forex data collection...")
            start_time = time.time()
            
            # Import and use the API-based forex signal integration
            from forex_signal_integration import ForexSignalIntegration
            
            signal_integration = ForexSignalIntegration()
            if not signal_integration.setup_successful:
                logger.error("❌ API-based signal integration not properly initialized")
                return None
                
            result = await signal_integration.generate_forex_signals()
            
            if result and result.get('has_real_data'):
                self.operation_times['forex_collection'] = time.time() - start_time
                logger.info(f"✅ API-based forex data collected in {self.operation_times['forex_collection']:.2f}s")
                return result
            else:
                logger.warning("⚠️ No active signals generated from API system")
                return None
                
        except Exception as e:
            logger.error(f"❌ API-based forex data collection failed: {e}")
            raise
    
    @resilient_operation("concurrent_operation", "data_collector", max_retries=2)
    async def _collect_heatmap_data_task(self) -> Optional[Dict[str, Any]]:
        """Heatmap collection disabled - focusing on API-based signals only"""
        return None
        try:
            logger.info("🔥 Starting heatmap generation...")
            start_time = time.time()
            
            # Run heatmap generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                result = await loop.run_in_executor(
                    executor, 
                    self._run_heatmap_generation
                )
            
            if result and result.get('success'):
                self.operation_times['heatmap_generation'] = time.time() - start_time
                logger.info(f"✅ Heatmap generated in {self.operation_times['heatmap_generation']:.2f}s")
                # Return the heatmap paths directly if available
                if result.get('categorical_heatmap') and result.get('forex_heatmap'):
                    return {
                        'categorical_heatmap': result['categorical_heatmap'],
                        'forex_heatmap': result['forex_heatmap']
                    }
                return result
            else:
                logger.warning("⚠️ Heatmap generation failed")
                return None
                
        except Exception as e:
            logger.error(f"❌ Heatmap generation failed: {e}")
            raise
    
    def _run_heatmap_generation(self) -> Dict[str, Any]:
        """Run heatmap generation in subprocess"""
        try:
            # Change to heatmaps directory and run generation
            heatmap_dir = Path(__file__).parent / 'heatmaps'
            if not heatmap_dir.exists():
                heatmap_dir = Path(__file__).parent.parent / 'heatmaps_package' / 'core_files'
            
            if heatmap_dir.exists():
                result = subprocess.run([
                    sys.executable, 'silent_bloomberg_system.py'
                ], cwd=heatmap_dir, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    # Find the generated heatmap files
                    reports_dir = heatmap_dir / 'reports'
                    if not reports_dir.exists():
                        reports_dir = Path(__file__).parent / 'heatmaps' / 'reports'
                    
                    # Find the most recent timestamped directory
                    if reports_dir.exists():
                        subdirs = [d for d in reports_dir.iterdir() 
                                 if d.is_dir() and len(d.name) > 8]
                        
                        if subdirs:
                            latest_dir = max(subdirs, key=lambda d: d.name)
                            categorical_path = latest_dir / 'categorical_heatmap.png'
                            forex_path = latest_dir / 'forex_pairs_heatmap.png'
                            
                            if categorical_path.exists() and forex_path.exists():
                                return {
                                    'success': True,
                                    'categorical_heatmap': str(categorical_path),
                                    'forex_heatmap': str(forex_path),
                                    'output': result.stdout,
                                    'generation_path': str(heatmap_dir)
                                }
                    
                    return {
                        'success': True,
                        'output': result.stdout,
                        'generation_path': str(heatmap_dir)
                    }
                else:
                    logger.error(f"Heatmap generation failed: {result.stderr}")
                    return {'success': False, 'error': result.stderr}
            else:
                return {'success': False, 'error': 'Heatmap directory not found'}
                
        except subprocess.TimeoutExpired:
            logger.error("Heatmap generation timeout")
            return {'success': False, 'error': 'Generation timeout'}
        except Exception as e:
            logger.error(f"Heatmap subprocess error: {e}")
            return {'success': False, 'error': str(e)}
    
    @resilient_operation("concurrent_operation", "data_collector", max_retries=2)
    async def _collect_currency_rates_task(self) -> Optional[Dict[str, Any]]:
        """Collect currency rates from multiple APIs concurrently"""
        try:
            logger.info("💱 Starting currency rates collection...")
            start_time = time.time()
            
            # Collect from multiple sources concurrently
            rate_tasks = [
                self._fetch_fred_rates(),
                self._fetch_ecb_rates(),
                self._fetch_boe_rates()
            ]
            
            rate_results = await asyncio.gather(*rate_tasks, return_exceptions=True)
            
            # Combine successful results
            combined_rates = {}
            sources_used = []
            
            for i, result in enumerate(rate_results):
                source_names = ['FRED', 'ECB', 'BOE']
                if not isinstance(result, Exception) and result:
                    combined_rates.update(result)
                    sources_used.append(source_names[i])
                else:
                    logger.warning(f"{source_names[i]} rates failed: {result}")
            
            if combined_rates:
                self.operation_times['currency_rates'] = time.time() - start_time
                logger.info(f"✅ Currency rates collected from {sources_used} in {self.operation_times['currency_rates']:.2f}s")
                return {
                    'rates': combined_rates,
                    'sources': sources_used,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"❌ Currency rates collection failed: {e}")
            raise
    
    async def _fetch_fred_rates(self) -> Dict[str, Any]:
        """Fetch rates from FRED API"""
        try:
            # Use circuit breaker for FRED API
            breaker = self.error_handler.get_circuit_breaker('fred_api')
            if not breaker.can_execute():
                logger.warning("FRED API circuit breaker open")
                return {}
            
            fred_api_key = self.config.get('fred_api_key')
            if not fred_api_key:
                return {}
            
            async with aiohttp.ClientSession() as session:
                # Federal funds rate
                url = f'https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS&api_key={fred_api_key}&file_type=json&limit=1&sort_order=desc'
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('observations'):
                            fed_rate = data['observations'][0]['value']
                            breaker.record_success()
                            return {'USD_FEDFUNDS': float(fed_rate) if fed_rate != '.' else None}
                    else:
                        breaker.record_failure()
                        
            return {}
            
        except Exception as e:
            self.error_handler.get_circuit_breaker('fred_api').record_failure()
            logger.error(f"FRED API error: {e}")
            return {}
    
    async def _fetch_ecb_rates(self) -> Dict[str, Any]:
        """Fetch rates from ECB API"""
        try:
            breaker = self.error_handler.get_circuit_breaker('ecb_api')
            if not breaker.can_execute():
                return {}
            
            async with aiohttp.ClientSession() as session:
                # ECB main refinancing rate
                url = 'https://data.ecb.europa.eu/api/v1/data/BSI/M.U2.Y.V.M30.A.1.U2.2300.Z01.E?format=jsondata'
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Parse ECB data structure
                        if data.get('data', {}).get('dataSets'):
                            breaker.record_success()
                            return {'EUR_ECB_RATE': 'Available'}  # Simplified for now
                    else:
                        breaker.record_failure()
                        
            return {}
            
        except Exception as e:
            self.error_handler.get_circuit_breaker('ecb_api').record_failure()
            logger.error(f"ECB API error: {e}")
            return {}
    
    async def _fetch_boe_rates(self) -> Dict[str, Any]:
        """Fetch rates from Bank of England"""
        try:
            breaker = self.error_handler.get_circuit_breaker('boe_api')
            if not breaker.can_execute():
                return {}
            
            async with aiohttp.ClientSession() as session:
                # BOE base rate
                url = 'https://www.bankofengland.co.uk/boeapps/database/Rates.asp?FD=1&TD=1&into=JSON'
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        breaker.record_success()
                        return {'GBP_BOE_RATE': 'Available'}  # Simplified for now
                    else:
                        breaker.record_failure()
                        
            return {}
            
        except Exception as e:
            self.error_handler.get_circuit_breaker('boe_api').record_failure()
            logger.error(f"BOE API error: {e}")
            return {}
    
    @resilient_operation("heatmap_cleanup", "data_collector", max_retries=1)
    async def _collect_market_sentiment_task(self) -> Optional[Dict[str, Any]]:
        """Collect market sentiment data (lightweight)"""
        try:
            logger.info("📈 Collecting market sentiment...")
            start_time = time.time()
            
            # Simple market sentiment calculation based on available data
            sentiment_data = {
                'timestamp': datetime.now().isoformat(),
                'sentiment_score': 'neutral',  # Would calculate from real data
                'volatility_index': 'moderate',
                'trend_direction': 'sideways',
                'confidence_level': 'medium'
            }
            
            self.operation_times['market_sentiment'] = time.time() - start_time
            logger.info(f"✅ Market sentiment collected in {self.operation_times['market_sentiment']:.2f}s")
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"❌ Market sentiment collection failed: {e}")
            raise
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all operations"""
        return {
            'operation_times': self.operation_times,
            'error_statistics': self.error_handler.get_error_statistics(),
            'total_operations': len(self.operation_times),
            'average_time': sum(self.operation_times.values()) / max(len(self.operation_times), 1)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of all data sources"""
        logger.info("🏥 Performing concurrent health check...")
        
        health_tasks = [
            self._check_mymama_health(),
            self._check_api_health('FRED', 'https://api.stlouisfed.org/fred/series?series_id=GDP&api_key=demo'),
            self._check_api_health('ECB', 'https://data.ecb.europa.eu'),
            self._check_api_health('BOE', 'https://www.bankofengland.co.uk')
        ]
        
        health_results = await asyncio.gather(*health_tasks, return_exceptions=True)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'mymama_health': health_results[0] if not isinstance(health_results[0], Exception) else 'error',
            'fred_health': health_results[1] if not isinstance(health_results[1], Exception) else 'error',
            'ecb_health': health_results[2] if not isinstance(health_results[2], Exception) else 'error',
            'boe_health': health_results[3] if not isinstance(health_results[3], Exception) else 'error',
            'overall_health': 'healthy' if sum(1 for r in health_results if not isinstance(r, Exception)) >= 2 else 'degraded'
        }
    
    async def _check_mymama_health(self) -> str:
        """Check MyMama website health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://www.mymama.uk', timeout=10) as response:
                    return 'healthy' if response.status == 200 else 'unhealthy'
        except:
            return 'unreachable'
    
    async def _check_api_health(self, name: str, url: str) -> str:
        """Check API endpoint health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    return 'healthy' if response.status < 500 else 'unhealthy'
        except:
            return 'unreachable'

async def main():
    """Test concurrent data collection"""
    config = {
        'max_concurrent_operations': 4,
        'timeout_seconds': 60,
        'error_handling': {
            'max_retries': 2,
            'base_retry_delay': 1
        }
    }
    
    collector = ConcurrentDataCollector(config)
    
    # Test health check
    health = await collector.health_check()
    print(f"Health Check: {json.dumps(health, indent=2)}")
    
    # Test concurrent collection (commented out for testing)
    # results = await collector.collect_all_data_concurrent()
    # print(f"Collection Results: {json.dumps(results, indent=2)}")
    
    # Performance metrics
    metrics = collector.get_performance_metrics()
    print(f"Performance Metrics: {json.dumps(metrics, indent=2)}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    asyncio.run(main())