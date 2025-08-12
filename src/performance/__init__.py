"""
Performance utilities for the Stream Futebol Dashboard application.

This module contains performance monitoring and optimization tools
for tracking application performance and execution times.
"""

from .timer_performance import (
    time_tick,
    time_ui_update,
    time_json_operation,
    get_timer_monitor,
)

__all__ = [
    'time_tick',
    'time_ui_update',
    'time_json_operation',
    'get_timer_monitor',
]
