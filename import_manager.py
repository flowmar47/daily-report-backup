"""
Import Manager - Centralized module import handling with graceful fallbacks
"""

import logging
import importlib
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

class ImportManager:
    """Centralized import management with fallbacks"""
    
    def __init__(self):
        self.cached_modules = {}
        self.failed_imports = set()
    
    def safe_import(self, module_path: str, fallback_paths: list = None, 
                   class_name: str = None) -> Optional[Any]:
        """
        Safely import module with fallback options
        
        Args:
            module_path: Primary module path to import
            fallback_paths: Alternative paths to try
            class_name: Specific class to import from module
            
        Returns:
            Imported module/class or None if all fail
        """
        if module_path in self.cached_modules:
            return self.cached_modules[module_path]
        
        if module_path in self.failed_imports:
            return None
        
        all_paths = [module_path] + (fallback_paths or [])
        
        for path in all_paths:
            try:
                module = importlib.import_module(path)
                
                if class_name:
                    result = getattr(module, class_name, None)
                    if result is None:
                        logger.warning(f"Class {class_name} not found in {path}")
                        continue
                else:
                    result = module
                
                self.cached_modules[module_path] = result
                logger.info(f"✅ Successfully imported {path}{f'.{class_name}' if class_name else ''}")
                return result
                
            except ImportError as e:
                logger.debug(f"Failed to import {path}: {e}")
                continue
            except AttributeError as e:
                logger.debug(f"Class {class_name} not found in {path}: {e}")
                continue
        
        logger.error(f"❌ Failed to import {module_path} and all fallbacks")
        self.failed_imports.add(module_path)
        return None
    
    def get_scrapers(self) -> Dict[str, Any]:
        """Get all available scrapers"""
        scrapers = {}
        
        # MyMama scraper variants
        mymama_scraper = self.safe_import(
            'real_only_mymama_scraper',
            fallback_paths=['mymama_scraper', 'scrapers.mymama_scraper'],
            class_name='RealOnlyMyMamaScraper'
        )
        if mymama_scraper:
            scrapers['mymama'] = mymama_scraper
        
        return scrapers
    
    def get_security_utils(self) -> Dict[str, Any]:
        """Get security utility classes"""
        utils = {}
        
        # Try different import paths
        security_module = self.safe_import(
            'security_utils',
            fallback_paths=['security-utils', 'utils.security_utils']
        )
        
        if security_module:
            for util_name in ['DataSanitizer', 'RateLimiter', 'HeaderManager', 
                             'SessionManager', 'ProxyManager', 'CAPTCHAHandler']:
                util_class = getattr(security_module, util_name, None)
                if util_class:
                    utils[util_name.lower()] = util_class
        
        return utils
    
    def get_parsers(self) -> Dict[str, Any]:
        """Get parser classes"""
        parsers = {}
        
        utils_module = self.safe_import('utils')
        if utils_module:
            for parser_name in ['ForexParser', 'ReportFormatter', 'ValidationHelper']:
                parser_class = getattr(utils_module, parser_name, None)
                if parser_class:
                    parsers[parser_name.lower()] = parser_class
        
        return parsers

# Global instance
import_manager = ImportManager()