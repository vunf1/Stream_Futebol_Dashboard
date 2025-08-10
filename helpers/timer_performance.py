# helpers/timer_performance.py
import time
import threading
from typing import Dict, List, Optional, Callable
from collections import defaultdict
import logging

class TimerPerformanceMonitor:
    """Performance monitoring specifically for timer components"""
    
    def __init__(self, instance_id: str):
        self.instance_id = instance_id
        self.logger = logging.getLogger(f'TimerPerformance-{instance_id}')
        
        # Performance metrics
        self.tick_times = []
        self.ui_update_times = []
        self.json_operation_times = []
        self.memory_usage = []
        
        # Configuration
        self.max_history = 100
        self.slow_threshold = 16.0  # 16ms threshold for slow operations
        
        # Thread safety
        self._lock = threading.Lock()
        
    def record_tick_time(self, duration_ms: float):
        """Record timer tick performance"""
        with self._lock:
            self.tick_times.append(duration_ms)
            if len(self.tick_times) > self.max_history:
                self.tick_times.pop(0)
            
            if duration_ms > self.slow_threshold:
                self.logger.warning(f"Slow timer tick: {duration_ms:.2f}ms")
    
    def record_ui_update_time(self, duration_ms: float):
        """Record UI update performance"""
        with self._lock:
            self.ui_update_times.append(duration_ms)
            if len(self.ui_update_times) > self.max_history:
                self.ui_update_times.pop(0)
            
            if duration_ms > self.slow_threshold:
                self.logger.warning(f"Slow UI update: {duration_ms:.2f}ms")
    
    def record_json_operation_time(self, duration_ms: float):
        """Record JSON operation performance"""
        with self._lock:
            self.json_operation_times.append(duration_ms)
            if len(self.json_operation_times) > self.max_history:
                self.json_operation_times.pop(0)
            
            if duration_ms > self.slow_threshold:
                self.logger.warning(f"Slow JSON operation: {duration_ms:.2f}ms")
    
    def get_performance_stats(self) -> Dict[str, any]: # type: ignore
        """Get comprehensive performance statistics"""
        with self._lock:
            stats = {
                'instance_id': self.instance_id,
                'tick_count': len(self.tick_times),
                'ui_update_count': len(self.ui_update_times),
                'json_operation_count': len(self.json_operation_times),
            }
            
            if self.tick_times:
                stats.update({
                    'avg_tick_time': sum(self.tick_times) / len(self.tick_times),
                    'max_tick_time': max(self.tick_times),
                    'min_tick_time': min(self.tick_times),
                })
            
            if self.ui_update_times:
                stats.update({
                    'avg_ui_update_time': sum(self.ui_update_times) / len(self.ui_update_times),
                    'max_ui_update_time': max(self.ui_update_times),
                    'min_ui_update_time': min(self.ui_update_times),
                })
            
            if self.json_operation_times:
                stats.update({
                    'avg_json_operation_time': sum(self.json_operation_times) / len(self.json_operation_times),
                    'max_json_operation_time': max(self.json_operation_times),
                    'min_json_operation_time': min(self.json_operation_times),
                })
            
            return stats
    
    def log_performance_summary(self):
        """Log a summary of performance metrics"""
        stats = self.get_performance_stats()
        
        summary = f"Timer {self.instance_id} Performance Summary:\n"
        if 'avg_tick_time' in stats:
            summary += f"  Tick: avg={stats['avg_tick_time']:.2f}ms, max={stats['max_tick_time']:.2f}ms\n"
        if 'avg_ui_update_time' in stats:
            summary += f"  UI Updates: avg={stats['avg_ui_update_time']:.2f}ms, max={stats['max_ui_update_time']:.2f}ms\n"
        if 'avg_json_operation_time' in stats:
            summary += f"  JSON Ops: avg={stats['avg_json_operation_time']:.2f}ms, max={stats['max_json_operation_time']:.2f}ms\n"
        
        self.logger.info(summary)
    
    def clear_history(self):
        """Clear performance history"""
        with self._lock:
            self.tick_times.clear()
            self.ui_update_times.clear()
            self.json_operation_times.clear()
            self.memory_usage.clear()

# Performance decorators
def time_tick(func):
    """Decorator to time timer tick operations"""
    def wrapper(self, *args, **kwargs):
        start_time = time.perf_counter()
        result = func(self, *args, **kwargs)
        end_time = time.perf_counter()
        
        duration_ms = (end_time - start_time) * 1000
        if hasattr(self, 'performance_monitor'):
            self.performance_monitor.record_tick_time(duration_ms)
        
        return result
    return wrapper

def time_ui_update(func):
    """Decorator to time UI update operations"""
    def wrapper(self, *args, **kwargs):
        start_time = time.perf_counter()
        result = func(self, *args, **kwargs)
        end_time = time.perf_counter()
        
        duration_ms = (end_time - start_time) * 1000
        if hasattr(self, 'performance_monitor'):
            self.performance_monitor.record_ui_update_time(duration_ms)
        
        return result
    return wrapper

def time_json_operation(func):
    """Decorator to time JSON operations"""
    def wrapper(self, *args, **kwargs):
        start_time = time.perf_counter()
        result = func(self, *args, **kwargs)
        end_time = time.perf_counter()
        
        duration_ms = (end_time - start_time) * 1000
        if hasattr(self, 'performance_monitor'):
            self.performance_monitor.record_json_operation_time(duration_ms)
        
        return result
    return wrapper

# Global performance registry
_timer_monitors = {}
_monitor_lock = threading.Lock()

def get_timer_monitor(instance_id: str) -> TimerPerformanceMonitor:
    """Get or create a timer performance monitor"""
    with _monitor_lock:
        if instance_id not in _timer_monitors:
            _timer_monitors[instance_id] = TimerPerformanceMonitor(instance_id)
        return _timer_monitors[instance_id]

def get_all_timer_stats() -> Dict[str, any]: # type: ignore
    """Get performance stats for all timer instances"""
    with _monitor_lock:
        return {instance_id: monitor.get_performance_stats() 
                for instance_id, monitor in _timer_monitors.items()}

def log_all_timer_performance():
    """Log performance summary for all timer instances"""
    with _monitor_lock:
        for monitor in _timer_monitors.values():
            monitor.log_performance_summary()

def clear_all_timer_history():
    """Clear performance history for all timer instances"""
    with _monitor_lock:
        for monitor in _timer_monitors.values():
            monitor.clear_history()
