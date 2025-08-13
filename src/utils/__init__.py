"""
General utilities for the Stream Futebol Dashboard application.

This module contains miscellaneous utility functions that provide
common functionality across the application.
"""

from .date_time_provider import DateTimeProvider
from .online_time_provider import (
    OnlineTimeProvider,
    get_online_time_provider,
    get_current_utc_time,
    get_current_portugal_time,
    is_time_online,
    get_time_source_info
)

__all__ = [
    'DateTimeProvider',
    'OnlineTimeProvider',
    'get_online_time_provider',
    'get_current_utc_time',
    'get_current_portugal_time',
    'is_time_online',
    'get_time_source_info',
]

