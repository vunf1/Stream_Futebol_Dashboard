# helpers/timer_performance.py
import time
from typing import Callable

# Performance decorators - simplified version
def time_tick(func):
    """Decorator to time timer tick operations"""
    def wrapper(self, *args, **kwargs):
        start_time = time.perf_counter()
        result = func(self, *args, **kwargs)
        end_time = time.perf_counter()
        
        duration_ms = (end_time - start_time) * 1000
        # Optional: log slow operations (over 16ms)
        if duration_ms > 16.0:
            print(f"Slow timer tick: {duration_ms:.2f}ms")
        
        return result
    return wrapper

def time_ui_update(func):
    """Decorator to time UI update operations"""
    def wrapper(self, *args, **kwargs):
        start_time = time.perf_counter()
        result = func(self, *args, **kwargs)
        end_time = time.perf_counter()
        
        duration_ms = (end_time - start_time) * 1000
        # Optional: log slow operations (over 16ms)
        if duration_ms > 16.0:
            print(f"Slow UI update: {duration_ms:.2f}ms")
        
        return result
    return wrapper

def time_json_operation(func):
    """Decorator to time JSON operations"""
    def wrapper(self, *args, **kwargs):
        start_time = time.perf_counter()
        result = func(self, *args, **kwargs)
        end_time = time.perf_counter()
        
        duration_ms = (end_time - start_time) * 1000
        # Optional: log slow operations (over 16ms)
        if duration_ms > 16.0:
            print(f"Slow JSON operation: {duration_ms:.2f}ms")
        
        return result
    return wrapper

# Simple monitor function for compatibility
def get_timer_monitor(instance_id: str):
    """Dummy function for compatibility - returns None"""
    return None
