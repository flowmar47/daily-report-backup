"""
Stock Alerts Package - Unusual Volume and After-Hours Activity Detection

This package provides real-time stock monitoring for:
- Unusual volume detection (relative to historical averages)
- Pre-market activity monitoring (4:00 AM - 9:30 AM ET)
- After-hours activity monitoring (4:00 PM - 8:00 PM ET)
- Price spike/drop detection during extended hours
"""

__version__ = "1.0.0"
__author__ = "Daily Report System"

from .core.config import StockAlertSettings, get_stock_settings
from .data.models import StockData, VolumeAlert, ExtendedHoursAlert
from .detection.volume_analyzer import VolumeAnalyzer
from .detection.extended_hours import ExtendedHoursMonitor
from .fetchers.stock_fetcher import StockDataFetcher

__all__ = [
    "StockAlertSettings",
    "get_stock_settings",
    "StockData",
    "VolumeAlert",
    "ExtendedHoursAlert",
    "VolumeAnalyzer",
    "ExtendedHoursMonitor",
    "StockDataFetcher",
]
