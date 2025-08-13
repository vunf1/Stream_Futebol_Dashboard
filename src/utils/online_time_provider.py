"""
Local Time Provider
Provides date/time using local system time with Portugal timezone.
"""

import time
from datetime import datetime, timezone
from typing import Optional
import pytz

class LocalTimeProvider:
    """
    Provides date/time using local system time with Portugal timezone.
    
    Features:
    - Fast local time access
    - Portugal timezone support
    - No external dependencies or API calls
    """
    
    def __init__(self):
        """Initialize the local time provider."""
        self.portugal_tz = pytz.timezone('Europe/Lisbon')
        
    def get_current_time(self) -> datetime:
        """
        Get current time using local system time.
        
        Returns:
            Current datetime in Portugal timezone (Europe/Lisbon)
        """
        return datetime.now(self.portugal_tz)
    
    def get_current_utc_time(self) -> datetime:
        """
        Get current UTC time.
        
        Returns:
            Current datetime in UTC
        """
        return datetime.now(timezone.utc)
    
    def get_current_portugal_time(self) -> datetime:
        """
        Get current time in Portugal timezone.
        
        Returns:
            Current datetime in Portugal timezone
        """
        return self.get_current_time()
    
    def is_time_online(self) -> bool:
        """
        Always returns False since this is a local-only provider.
        
        Returns:
            False (local time only)
        """
        return False
    
    def get_time_source_info(self) -> str:
        """
        Get information about the time source.
        
        Returns:
            Description of the time source
        """
        return "Local (offline)"


# Global instance
_local_time_provider = LocalTimeProvider()

# Convenience functions
def get_local_time_provider() -> LocalTimeProvider:
    """Get the global local time provider instance."""
    return _local_time_provider

def get_current_utc_time() -> datetime:
    """Get current UTC time."""
    return _local_time_provider.get_current_utc_time()

def get_current_portugal_time() -> datetime:
    """Get current time in Portugal timezone."""
    return _local_time_provider.get_current_portugal_time()

def is_time_online() -> bool:
    """Check if time is from online source (always False for local provider)."""
    return False

def get_time_source_info() -> str:
    """Get information about the time source."""
    return "Local (offline)"

# Alias for backward compatibility
# Backward compatibility alias removed - use LocalTimeProvider directly
get_online_time_provider = get_local_time_provider
