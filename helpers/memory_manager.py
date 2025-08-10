# helpers/memory_manager.py
import gc
import psutil
import threading
import time
from typing import Dict, List, Optional, Callable
from collections import defaultdict
import logging

class MemoryManager:
    """Memory management utility for optimizing memory usage"""
    
    def __init__(self, auto_cleanup: bool = True, cleanup_interval: int = 300):
        self.auto_cleanup = auto_cleanup
        self.cleanup_interval = cleanup_interval
        self.cleanup_thread = None
        self.running = False
        self.memory_threshold = 0.8  # 80% memory usage threshold
        self.logger = logging.getLogger('MemoryManager')
        
        # Track memory usage over time
        self.memory_history = []
        self.max_history = 100
        
        if self.auto_cleanup:
            self.start_auto_cleanup()
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss / 1024 / 1024,  # MB
            'vms': memory_info.vms / 1024 / 1024,  # MB
            'percent': process.memory_percent(),
            'available': psutil.virtual_memory().available / 1024 / 1024,  # MB
            'total': psutil.virtual_memory().total / 1024 / 1024  # MB
        }
    
    def record_memory_usage(self):
        """Record current memory usage"""
        usage = self.get_memory_usage()
        self.memory_history.append({
            'timestamp': time.time(),
            'usage': usage
        })
        
        # Keep history size manageable
        if len(self.memory_history) > self.max_history:
            self.memory_history.pop(0)
    
    def should_cleanup(self) -> bool:
        """Check if memory cleanup is needed"""
        usage = self.get_memory_usage()
        return usage['percent'] > (self.memory_threshold * 100)
    
    def cleanup_memory(self, force: bool = False):
        """Perform memory cleanup"""
        if not force and not self.should_cleanup():
            return
        
        self.logger.info("Starting memory cleanup...")
        
        # Force garbage collection
        collected = gc.collect()
        
        # Record cleanup
        self.record_memory_usage()
        
        self.logger.info(f"Memory cleanup completed. Collected {collected} objects.")
    
    def start_auto_cleanup(self):
        """Start automatic memory cleanup thread"""
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            return
        
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def stop_auto_cleanup(self):
        """Stop automatic memory cleanup"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=1)
    
    def _cleanup_loop(self):
        """Background cleanup loop"""
        while self.running:
            try:
                self.cleanup_memory()
                time.sleep(self.cleanup_interval)
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                time.sleep(60)  # Wait before retrying
    
    def get_memory_stats(self) -> Dict[str, any]: # type: ignore
        """Get comprehensive memory statistics"""
        current = self.get_memory_usage()
        
        if not self.memory_history:
            return current
        
        # Calculate trends
        recent = self.memory_history[-10:] if len(self.memory_history) >= 10 else self.memory_history
        avg_rss = sum(h['usage']['rss'] for h in recent) / len(recent)
        avg_percent = sum(h['usage']['percent'] for h in recent) / len(recent)
        
        return {
            **current,
            'avg_rss': avg_rss,
            'avg_percent': avg_percent,
            'history_count': len(self.memory_history),
            'trend': 'increasing' if len(self.memory_history) >= 2 and 
                    self.memory_history[-1]['usage']['rss'] > self.memory_history[-2]['usage']['rss'] 
                    else 'stable' if len(self.memory_history) >= 2 else 'unknown'
        }
    
    def log_memory_stats(self):
        """Log current memory statistics"""
        stats = self.get_memory_stats()
        self.logger.info(f"Memory Stats: RSS={stats['rss']:.1f}MB, "
                        f"Percent={stats['percent']:.1f}%, "
                        f"Available={stats['available']:.1f}MB, "
                        f"Trend={stats['trend']}")

# Global instance
_memory_manager = MemoryManager()

def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage"""
    return _memory_manager.get_memory_usage()

def cleanup_memory(force: bool = False):
    """Perform memory cleanup"""
    _memory_manager.cleanup_memory(force)

def should_cleanup_memory() -> bool:
    """Check if memory cleanup is needed"""
    return _memory_manager.should_cleanup()

def log_memory_stats():
    """Log memory statistics"""
    _memory_manager.log_memory_stats()

def get_memory_stats() -> Dict[str, any]: # type: ignore
    """Get comprehensive memory statistics"""
    return _memory_manager.get_memory_stats()

# Context manager for memory tracking
class MemoryTracker:
    def __init__(self, name: str):
        self.name = name
        self.start_memory = None
    
    def __enter__(self):
        self.start_memory = get_memory_usage()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_memory:
            end_memory = get_memory_usage()
            diff = end_memory['rss'] - self.start_memory['rss']
            if abs(diff) > 1.0:  # Only log if difference is > 1MB
                logging.getLogger('MemoryTracker').info(
                    f"{self.name}: Memory change: {diff:+.1f}MB "
                    f"({self.start_memory['rss']:.1f}MB → {end_memory['rss']:.1f}MB)"
                )
