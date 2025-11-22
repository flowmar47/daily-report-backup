"""Detection modules for unusual market activity"""

from .volume_analyzer import VolumeAnalyzer
from .extended_hours import ExtendedHoursMonitor

__all__ = ["VolumeAnalyzer", "ExtendedHoursMonitor"]
