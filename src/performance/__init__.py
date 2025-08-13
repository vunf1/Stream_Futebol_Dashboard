"""
Performance utilities for the Stream Futebol Dashboard application.

This module contains performance monitoring tools and timing decorators
for measuring operation performance.
"""

from .timer_performance import (
    time_ui_update,
    time_json_operation,
)

__all__ = [
    'time_ui_update',
    'time_json_operation',
]
