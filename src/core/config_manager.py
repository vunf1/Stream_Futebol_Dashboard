# helpers/config_manager.py
import json
import os
from typing import Any, Dict, Optional
from pathlib import Path
from .logger import get_logger

class ConfigManager:
    """Centralized configuration management for performance settings"""
    
    def __init__(self, config_file: str = "performance_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_default_config()
        self._load_config()
        self._log = get_logger(__name__)
        # Precompute allow/forbid sets
        self._allowed_top_keys = set(self.config.keys())
        self._allowed_teams_cache_keys = set(self.config.get("teams_cache", {}).keys())
        self._forbidden_keys_ci = {"admin_pin", "pin"}
        # Accept legacy/uppercase aliases from UI editor and map to internal keys
        self._alias_key_map = {
            "WINDOW_OPACITY": "window_opacity",
            "UI_UPDATE_DEBOUNCE": "ui_update_debounce",
            "ICON_CACHE_SIZE": "icon_cache_size",
            "WRITE_BUFFER_DELAY": "write_buffer_delay",
            # Server toggles (from Config Editor)
            "SERVER_WATCHDOG_ENABLED": "server_watchdog_enabled",
            "SERVER_HEALTH_CHECK_ENABLED": "server_health_check_enabled",
        }
    
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
            "performance_history_size": 1000, # History size for perf metrics
            
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

            # Server health/watchdog toggles (UI controllable)
            "server_watchdog_enabled": False,
            "server_health_check_enabled": True,
        }
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    # Sanitize incoming config
                    safe = self._sanitize_updates(file_config)
                    self.config.update(safe)
            except Exception as e:
                # Log but continue with defaults
                get_logger(__name__).warning("config_load_failed", exc_info=True)
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self._log.warning("config_save_failed", exc_info=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value (enforces allow/forbid rules)"""
        if self._is_forbidden_key(key):
            self._log.warning("config_update_forbidden_key", extra={"key": key})
            return
        if key not in self._allowed_top_keys:
            self._log.warning("config_update_unknown_key", extra={"key": key})
            return
        # Special handling for nested dicts
        if key == "teams_cache" and isinstance(value, dict):
            safe_tc = {k: v for k, v in value.items() if k in self._allowed_teams_cache_keys}
            self.config[key] = {**self.config.get(key, {}), **safe_tc}
        else:
            self.config[key] = value
    
    def update(self, updates: Dict[str, Any]):
        """Update multiple configuration values (enforces allow/forbid rules)"""
        safe = self._sanitize_updates(updates)
        if not safe:
            return
        # Merge respecting nested teams_cache
        for k, v in safe.items():
            if k == "teams_cache" and isinstance(v, dict):
                base = self.config.get("teams_cache", {})
                base.update(v)
                self.config["teams_cache"] = base
            else:
                self.config[k] = v
        self._log.info("config_updated", extra={"keys": list(safe.keys())})

    # ---- helpers ----
    def _sanitize_updates(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        safe: Dict[str, Any] = {}
        for orig_key, value in updates.items():
            key = self._alias_key_map.get(orig_key, orig_key)
            # Forbid dangerous keys (case-insensitive)
            if self._is_forbidden_key(key) or self._is_forbidden_key(orig_key):
                self._log.warning("config_update_forbidden_key", extra={"key": orig_key})
                continue
            # Unknown top-level keys are ignored
            if key not in self._allowed_top_keys:
                self._log.warning("config_update_unknown_key", extra={"key": orig_key})
                continue
            if key == "teams_cache":
                if isinstance(value, dict):
                    tc: Dict[str, Any] = {}
                    for tk, tv in value.items():
                        if tk in self._allowed_teams_cache_keys and not self._is_forbidden_key(tk):
                            tc[tk] = tv
                        else:
                            self._log.warning("config_update_unknown_teams_cache_key", extra={"key": tk})
                    if tc:
                        safe[key] = tc
                else:
                    self._log.warning("config_update_invalid_type", extra={"key": key})
            else:
                safe[key] = value
        return safe

    def _is_forbidden_key(self, key: str) -> bool:
        try:
            return key.lower() in self._forbidden_keys_ci
        except Exception:
            return False
    
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
