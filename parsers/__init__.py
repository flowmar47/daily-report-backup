"""
Parser modules for extracting structured data from web content.
"""

from .forex_parser import ForexParser
from .options_parser import OptionsParser
from .table_parser import TableParser
from .earnings_parser import EarningsParser

__all__ = ['ForexParser', 'OptionsParser', 'TableParser', 'EarningsParser']