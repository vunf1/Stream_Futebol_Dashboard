from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from src.core.env_loader import ensure_env_loaded
from src.core import get_env
from src.core import save_teams_to_json, load_teams_from_json
from src.notification import show_message_notification
# Performance monitoring removed - keeping core optimizations
import threading
import time
from typing import Optional, Dict
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from src.config.settings import AppConfig
from src.core.logger import get_logger

# Global connection pool
_mongo_client = None
_mongo_client_lock = threading.Lock()

# ─── SmartTeamCache ─────────────────────────────────────────────────────────
class SmartTeamCache:
    """Enhanced cache with selective invalidation and adaptive TTL"""
    
    def __init__(self, base_ttl: int = 300):
        self._cache: Dict[str, str] = {}
        self._cache_timestamp = 0
        self._base_ttl = base_ttl
        self._dirty_flags = set()  # Track which teams changed
        self._usage_count = 0
        self._last_access = time.time()
        self._lock = threading.Lock()
    
    def get_ttl(self) -> int:
        """Adapt TTL based on usage frequency"""
        with self._lock:
            current_time = time.time()
            time_since_access = current_time - self._last_access
            
            if self._usage_count > 10 and time_since_access < 60:
                # High usage, extend cache
                return min(self._base_ttl * 2, 1800)  # Up to 30 minutes
            elif self._usage_count < 3:
                # Low usage, shorten cache
                return max(self._base_ttl // 2, 60)   # Minimum 1 minute
            
            return self._base_ttl
    
    def is_valid(self) -> bool:
        """Check if cache is still valid"""
        current_time = time.time()
        return (bool(self._cache) and 
                (current_time - self._cache_timestamp) < self.get_ttl())
    
    def get_team(self, team_name: str) -> Optional[str]:
        """Get single team with selective cache check"""
        team_key = team_name.strip().upper()
        with self._lock:
            if team_key not in self._dirty_flags:
                self._record_access()
                return self._cache.get(team_key)
        return None
    
    def get_all(self) -> Dict[str, str]:
        """Get all teams from cache"""
        with self._lock:
            self._record_access()
            return self._cache.copy() if self._cache else {}
    
    def update_team(self, team_name: str, abbreviation: str):
        """Update single team in cache"""
        team_key = team_name.strip().upper()
        with self._lock:
            self._cache[team_key] = abbreviation.strip().upper()
            # Mark this team as fresh
            self._dirty_flags.discard(team_key)

    
    def invalidate_team(self, team_name: str):
        """Selective invalidation - only mark specific team as dirty"""
        team_key = team_name.strip().upper()
        with self._lock:
            self._dirty_flags.add(team_key)

    
    def invalidate_all(self):
        """Invalidate entire cache"""
        with self._lock:
            self._cache.clear()
            self._cache_timestamp = 0
            self._dirty_flags.clear()
    
    def set_teams(self, teams: Dict[str, str]):
        """Set all teams and mark cache as fresh"""
        with self._lock:
            self._cache = {str(k).upper(): str(v).upper() for k, v in teams.items()}
            self._cache_timestamp = time.time()
            self._dirty_flags.clear()
    
    def _record_access(self):
        """Record cache access for TTL optimization"""
        self._usage_count += 1
        self._last_access = time.time()

# Global smart cache instance
_teams_cache = SmartTeamCache(base_ttl=int(getattr(AppConfig, "UI_UPDATE_DEBOUNCE", 50)) * 6)
_teams_cache_timestamp = 0
_log = get_logger(__name__)


def _sanitize_mongo_uri(uri: str) -> str:
    """Ensure TLS is enabled for mongodb:// URIs; leave mongodb+srv intact.

    - mongodb+srv implies TLS by default; returned as-is
    - mongodb:// without tls/ssl query param -> add tls=true
    - mongodb:// with existing query -> preserve and append tls=true if missing
    """
    if not isinstance(uri, str):
        return uri
    u = uri.strip()
    if u.lower().startswith("mongodb+srv://"):
        return u
    if u.lower().startswith("mongodb://"):
        parts = urlparse(u)
        params = dict(parse_qsl(parts.query, keep_blank_values=True))
        if "tls" not in params and "ssl" not in params:
            params["tls"] = "true"
        new_query = urlencode(params, doseq=True)
        u = urlunparse((parts.scheme, parts.netloc, parts.path or "", parts.params, new_query, parts.fragment))
        return u
    return u

def _get_mongo_client():
    """Get or create MongoDB client with connection pooling"""
    global _mongo_client
    
    # Ensure environment is loaded before accessing env vars
    ensure_env_loaded()
    
    with _mongo_client_lock:
        if _mongo_client is None:
            uri = _sanitize_mongo_uri(get_env("MONGO_URI"))
            _mongo_client = MongoClient(
                uri,
                maxPoolSize=10,  # Connection pool size
                minPoolSize=1,
                maxIdleTimeMS=30000,  # 30 seconds
                serverSelectionTimeoutMS=5000,  # 5 seconds timeout
                connectTimeoutMS=5000
            )
        return _mongo_client

# ─── MongoTeamManager ───────────────────────────────────────────────────────
class MongoTeamManager:
    def __init__(self):
        self.client = _get_mongo_client()
        
        db_name = get_env("MONGO_DB")
        self.db = self.client[db_name]

        coll_name = get_env("MONGO_COLLECTION")
        self.collection = self.db[coll_name]
        try:
            self.collection.create_index("name", unique=True)
        except Exception:
            try:
                _log.warning("mongo_index_create_failed", exc_info=True)
            except Exception:
                pass
        
        # Background sync thread for JSON updates
        self._json_sync_pending = False
        self._json_sync_lock = threading.Lock()

    def save_team(self, name: str, abbreviation: str) -> None:
        name_clean = name.strip().upper()
        abbr_clean = abbreviation.strip().upper()

        start_time = time.time()
        try:
            result = self.collection.update_one(
                {"name": name_clean},
                {"$set": {"abbreviation": abbr_clean}},
                upsert=True
            )
            
            # Record database write performance

            
            # Update cache incrementally instead of clearing all
            global _teams_cache
            _teams_cache.update_team(name_clean, abbr_clean)
            
            # Schedule background JSON update
            self._schedule_json_update()
            
            try:
                if result.upserted_id:
                    _log.info("team_inserted", extra={"name": name_clean})
                else:
                    _log.info("team_updated", extra={"name": name_clean})
            except Exception:
                pass
                
        except Exception as e:
            raise e

    def load_teams(self) -> dict[str, str]:
        global _teams_cache
        
        # Check smart cache first
        if _teams_cache.is_valid():
            try:
                _log.debug("teams_loaded_cache")
            except Exception:
                pass
            return _teams_cache.get_all()
        
        # Load from database with projection for better performance
        start_time = time.time()
        try:
            teams = {
                doc["name"]: doc["abbreviation"]
                for doc in self.collection.find(projection={"name": 1, "abbreviation": 1, "_id": 0})
            }
            
            # Record database query performance
            query_time = time.time() - start_time
            try:
                _log.debug("teams_query_ms", extra={"ms": int(query_time * 1000)})
            except Exception:
                pass
            # Update smart cache
            _teams_cache.set_teams(teams)
            
            try:
                _log.info("teams_loaded_db")
            except Exception:
                pass
            return teams
            
        except ConnectionFailure as e:
            try:
                _log.error("mongo_connection_failed", exc_info=True)
            except Exception:
                pass
            # Return cached data if available, even if expired
            cached_teams = _teams_cache.get_all()
            if cached_teams:
                try:
                    _log.warning("teams_loaded_stale_cache")
                except Exception:
                    pass
                return cached_teams
            return {}

    def get_abbreviation(self, name: str) -> str:
        name_clean = name.strip().upper()
        
        # Try smart cache first
        cached_abbr = _teams_cache.get_team(name_clean)
        if cached_abbr:
            return cached_abbr
        
        # Fallback to database query
        try:
            doc = self.collection.find_one(
                {"name": name_clean}, 
                projection={"abbreviation": 1, "_id": 0}
            )
            if doc:
                # Update cache with this team
                _teams_cache.update_team(name_clean, doc["abbreviation"])
                return doc["abbreviation"]
            return ""
        except ConnectionFailure:
            return ""

    def get_all_names(self) -> list[str]:
        # Use smart cached data if available
        cached_teams = _teams_cache.get_all()
        if cached_teams:
            return list(cached_teams.keys())
        
        # Fallback to database
        try:
            return [doc["name"] for doc in self.collection.find(
                projection={"name": 1, "_id": 0}
            )]
        except ConnectionFailure:
            return []

    def backup_to_json(self) -> None:
        """Optimized JSON backup with change detection"""
        teams = self.load_teams()
        
        # Load existing JSON to compare
        try:
            existing_teams = load_teams_from_json()
            if existing_teams == teams:
                try:
                    _log.debug("teams_json_up_to_date")
                except Exception:
                    pass
                return  # No changes, skip write
        except:
            pass  # JSON doesn't exist or is invalid
        
        # Only write if there are actual changes
        try:
            _log.info("teams_json_changed_updating")
        except Exception:
            pass
        save_teams_to_json(teams)

    def delete_team(self, name: str) -> bool:
        """Delete team from database and invalidate cache"""
        result = self.collection.delete_one({"name": name.strip().upper()})
        
        # Invalidate specific team in cache
        global _teams_cache
        _teams_cache.invalidate_team(name.strip().upper())
        
        # Schedule background JSON update
        self._schedule_json_update()
        
        return result.deleted_count > 0

    def _schedule_json_update(self):
        """Schedule JSON update in background thread to avoid blocking UI"""
        with self._json_sync_lock:
            if self._json_sync_pending:
                return  # Already scheduled
            
            self._json_sync_pending = True
            
            def background_sync():
                time.sleep(0.5)  # Small delay to batch multiple updates
                try:
                    self.backup_to_json()
                finally:
                    with self._json_sync_lock:
                        self._json_sync_pending = False
            
            # Use daemon thread to avoid blocking app shutdown
            sync_thread = threading.Thread(target=background_sync, daemon=True)
            sync_thread.start()