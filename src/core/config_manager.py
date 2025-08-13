# helpers/config_manager.py
import json
import os
from typing import Any, Dict, Optional
from pathlib import Path

class ConfigManager:
    """Centralized configuration management for performance settings"""
    
    def __init__(self, config_file: str = "performance_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_default_config()
        self._load_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values"""
        return {
            # File I/O settings
            "write_buffer_delay": 0.1,  # 100ms delay for write buffering
            "write_buffer_size": 100,   # Max items in write buffer
            
            # UI performance settings
            "ui_update_debounce": 50,   # 50ms debounce for UI updates
            "icon_cache_size": 50,      # Max icons in cache
            
            # Database settings
            "mongo_cache_ttl": 300,     # 5 minutes cache TTL
            "mongo_pool_size": 10,      # Connection pool size
            
            # Teams cache settings
            "teams_cache": {
                "base_ttl": 300,           # Base cache TTL
                "max_ttl": 1800,           # Maximum cache TTL
                "min_ttl": 60,             # Minimum cache TTL
                "batch_update_delay": 0.5, # Delay for batching updates
                "background_sync": True,    # Enable background JSON sync
                "preload_json": True,      # Preload JSON during startup
                "incremental_updates": True # Use incremental cache updates
            },
            
            # Memory management
            "memory_cleanup_interval": 300,  # 5 minutes
            "memory_threshold": 0.8,         # 80% memory usage threshold
            
            # Process management
            "process_batch_size": 3,         # Processes per batch
            "process_startup_delay": 0.05,   # 50ms delay between batches
            
            # Timer settings
            "timer_update_interval": 1000,   # 1 second timer updates
            
            # Notification settings
            "notification_poll_interval": 80,  # 80ms notification polling
            
            # Debug settings
            "debug_mode": False,
            "log_level": "INFO",
            
            # UI appearance settings
            "window_opacity": 0.95,  # Window transparency level (0.0 to 1.0)
        }
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
    
    def update(self, updates: Dict[str, Any]):
        """Update multiple configuration values"""
        self.config.update(updates)
    
    def get_performance_settings(self) -> Dict[str, Any]:
        """Get all performance-related settings"""
        performance_keys = [
            'write_buffer_delay', 'write_buffer_size', 'ui_update_debounce',
            'icon_cache_size', 'mongo_cache_ttl', 'mongo_pool_size',
            'memory_cleanup_interval', 'memory_threshold', 'process_batch_size',
            'process_startup_delay', 'timer_update_interval',
            'notification_poll_interval'
        ]
        return {key: self.config[key] for key in performance_keys}
    
    def optimize_for_performance(self):
        """Apply aggressive performance optimizations"""
        self.update({
            'write_buffer_delay': 0.05,      # 50ms delay
            'ui_update_debounce': 25,        # 25ms debounce
            'icon_cache_size': 100,          # Larger icon cache
            'mongo_cache_ttl': 600,          # 10 minutes cache
            'memory_cleanup_interval': 180,  # 3 minutes cleanup
            'process_startup_delay': 0.02,   # 20ms delay
            'notification_poll_interval': 50 # 50ms polling
        })
    
    def optimize_for_memory(self):
        """Apply memory optimization settings"""
        self.update({
            'icon_cache_size': 25,           # Smaller icon cache
            'memory_cleanup_interval': 120,  # 2 minutes cleanup
            'memory_threshold': 0.7,         # 70% threshold
            'performance_history_size': 500  # Smaller history
        })
    
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self.config = self._load_default_config()

# Global instance
_config_manager = ConfigManager()

def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value"""
    return _config_manager.get(key, default)

def set_config(key: str, value: Any):
    """Set configuration value"""
    _config_manager.set(key, value)

def update_config(updates: Dict[str, Any]):
    """Update multiple configuration values"""
    _config_manager.update(updates)

def save_config():
    """Save configuration to file"""
    _config_manager.save_config()

def get_performance_settings() -> Dict[str, Any]:
    """Get all performance-related settings"""
    return _config_manager.get_performance_settings()

def optimize_for_performance():
    """Apply aggressive performance optimizations"""
    _config_manager.optimize_for_performance()

def optimize_for_memory():
    """Apply memory optimization settings"""
    _config_manager.optimize_for_memory()
