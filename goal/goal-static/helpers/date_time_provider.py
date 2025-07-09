import time
from datetime import datetime

class DateTimeProvider:
    """
    Gives you the current date and/or time, but only refreshes once each second.

    Class Attributes:
        _cached_str (str | None):  
            The last full timestamp we made.
        _last_update (float):  
            When (in seconds since beginning) we last updated the cache.
        _refresh_sec (float):  
            How many seconds to wait before making a new timestamp.
    """
    _cached_str: str | None = None
    _last_update: float = 0.0
    _refresh_sec: float = 1.0

    @classmethod
    def get_datetime(cls) -> str:
        """
        "YYYY-MM-DD HH:MM:SS" 
        """
        now_ts = time.time()
        if (cls._cached_str is None
            or (now_ts - cls._last_update) >= cls._refresh_sec):
            cls._cached_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cls._last_update = now_ts
        return cls._cached_str 

    @classmethod
    def get_date(cls) -> str:
        """
        "YYYY-MM-DD".
        """
        return cls.get_datetime().split(" ")[0]

    @classmethod
    def get_time(cls) -> str:
        """
        "HH:MM:SS".
        """
        return cls.get_datetime().split(" ")[1]
