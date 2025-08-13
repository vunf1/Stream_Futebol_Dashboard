"""
Online Time Provider
Provides accurate date/time from online sources with fallback to local time when offline.
"""

import time
import requests
from datetime import datetime, timezone
from typing import Optional, Tuple
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

class OnlineTimeProvider:
    """
    Provides accurate date/time from online sources with fallback to local time.
    
    Features:
    - Multiple reliable time server sources
    - Automatic fallback when offline
    - Caching to reduce API calls
    - Thread-safe operations
    """
    
    # Reliable time servers to check (Portugal timezone)
    TIME_SERVERS = [
        "http://worldtimeapi.org/api/timezone/Europe/Lisbon",
        "https://timeapi.io/api/Time/current/zone?timeZone=Europe/Lisbon",
        "https://api.timezonedb.com/v2.1/get-time-zone?key=demo&format=json&by=zone&zone=Europe/Lisbon"
    ]
    
    def __init__(self, cache_duration: int = 300):
        """
        Initialize the online time provider.
        
        Args:
            cache_duration: How long to cache the online time in seconds (default: 5 minutes)
        """
        self.cache_duration = cache_duration
        self._cached_time = None
        self._cache_timestamp = 0
        self._lock = threading.Lock()
        self._session = requests.Session()
        # Set timeout for individual requests (not session-level)
        self._request_timeout = 5  # 5 second timeout for requests
        
    def get_current_time(self) -> datetime:
        """
        Get current time, preferring online sources with fallback to local time.
        
        Returns:
            Current datetime in Portugal timezone (Europe/Lisbon)
        """
        # Check cache first
        with self._lock:
            current_time = time.time()
            if (self._cached_time and 
                (current_time - self._cache_timestamp) < self.cache_duration):
                return self._cached_time
        
        # Try to get online time
        online_time = self._get_online_time()
        if online_time:
            with self._lock:
                self._cached_time = online_time
                self._cache_timestamp = current_time
            return online_time
        
        # Fallback to local time in Portugal timezone
        import pytz
        portugal_tz = pytz.timezone('Europe/Lisbon')
        return datetime.now(portugal_tz)
    
    def _get_online_time(self) -> Optional[datetime]:
        """
        Attempt to get time from online sources.
        
        Returns:
            UTC datetime if successful, None if all sources fail
        """
        try:
            # Use ThreadPoolExecutor to check multiple servers concurrently
            with ThreadPoolExecutor(max_workers=len(self.TIME_SERVERS)) as executor:
                # Submit all time server checks
                future_to_server = {
                    executor.submit(self._check_time_server, server): server 
                    for server in self.TIME_SERVERS
                }
                
                # Wait for first successful response (with timeout)
                for future in as_completed(future_to_server, timeout=10):
                    try:
                        result = future.result()
                        if result:
                            print(f"✅ Online time obtained from {future_to_server[future]}")
                            return result
                    except (TimeoutError, Exception) as e:
                        print(f"⚠️ Time server {future_to_server[future]} failed: {e}")
                        continue
                        
        except Exception as e:
            print(f"❌ All online time sources failed: {e}")
        
        return None
    
    def _check_time_server(self, server_url: str) -> Optional[datetime]:
        """
        Check a specific time server for current time.
        
        Args:
            server_url: URL of the time server to check
            
        Returns:
            UTC datetime if successful, None if failed
        """
        try:
            response = self._session.get(server_url, timeout=self._request_timeout)
            response.raise_for_status()
            data = response.json()
            
            # Parse different time server response formats
            if "datetime" in data:
                # worldtimeapi.org format
                dt_str = data["datetime"]
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                # Convert to Portugal timezone
                import pytz
                portugal_tz = pytz.timezone('Europe/Lisbon')
                return dt.astimezone(portugal_tz)
            
            elif "dateTime" in data:
                # timeapi.io format
                dt_str = data["dateTime"]
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                # Convert to Portugal timezone
                import pytz
                portugal_tz = pytz.timezone('Europe/Lisbon')
                return dt.astimezone(portugal_tz)
            
            elif "formatted" in data:
                # timezonedb format
                dt_str = data["formatted"]
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                # Convert to Portugal timezone
                import pytz
                portugal_tz = pytz.timezone('Europe/Lisbon')
                return dt.astimezone(portugal_tz)
            
            else:
                print(f"⚠️ Unknown time server response format from {server_url}")
                return None
                
        except Exception as e:
            print(f"⚠️ Failed to get time from {server_url}: {e}")
            return None
    
    def is_online(self) -> bool:
        """
        Check if we can reach any online time servers.
        
        Returns:
            True if online, False if offline
        """
        return self._get_online_time() is not None
    
    def get_time_source_info(self) -> Tuple[str, bool]:
        """
        Get information about the current time source.
        
        Returns:
            Tuple of (source_description, is_online)
        """
        with self._lock:
            if (self._cached_time and 
                (time.time() - self._cache_timestamp) < self.cache_duration):
                return "Online (cached)", True
        
        if self.is_online():
            return "Online (live)", True
        else:
            return "Local (offline)", False
    
    def force_refresh(self) -> datetime:
        """
        Force a refresh of the online time, ignoring cache.
        
        Returns:
            Current datetime from best available source
        """
        with self._lock:
            self._cached_time = None
            self._cache_timestamp = 0
        
        return self.get_current_time()


# Global instance for easy access
_global_time_provider = None

def get_online_time_provider() -> OnlineTimeProvider:
    """
    Get the global online time provider instance.
    
    Returns:
        Global OnlineTimeProvider instance
    """
    global _global_time_provider
    if _global_time_provider is None:
        _global_time_provider = OnlineTimeProvider()
    return _global_time_provider


def get_current_portugal_time() -> datetime:
    """
    Get current Portugal time using online sources with fallback.
    
    Returns:
        Current datetime in Portugal timezone (Europe/Lisbon)
    """
    return get_online_time_provider().get_current_time()


def get_current_utc_time() -> datetime:
    """
    Get current Portugal time using online sources with fallback.
    (Backward compatibility - returns Portugal time, not UTC)
    
    Returns:
        Current datetime in Portugal timezone (Europe/Lisbon)
    """
    return get_current_portugal_time()


def is_time_online() -> bool:
    """
    Check if time source is online.
    
    Returns:
        True if online, False if offline
    """
    return get_online_time_provider().is_online()


def get_time_source_info() -> Tuple[str, bool]:
    """
    Get information about the current time source.
    
    Returns:
        Tuple of (source_description, is_online)
    """
    return get_online_time_provider().get_time_source_info()
