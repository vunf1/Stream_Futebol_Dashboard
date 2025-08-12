from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from src.core.env_loader import ensure_env_loaded
from src.core import get_env
from src.core import save_teams_to_json
from src.notification import show_message_notification
import threading
import time

# Global connection pool
_mongo_client = None
_mongo_client_lock = threading.Lock()
_teams_cache = {}
_teams_cache_timestamp = 0
_cache_ttl = 300  # 5 minutes cache

def _get_mongo_client():
    """Get or create MongoDB client with connection pooling"""
    global _mongo_client
    
    # Ensure environment is loaded before accessing env vars
    ensure_env_loaded()
    
    with _mongo_client_lock:
        if _mongo_client is None:
            uri = get_env("MONGO_URI")
            _mongo_client = MongoClient(
                uri,
                maxPoolSize=10,  # Connection pool size
                minPoolSize=1,
                maxIdleTimeMS=30000,  # 30 seconds
                serverSelectionTimeoutMS=5000,  # 5 seconds timeout
                connectTimeoutMS=5000
            )
        return _mongo_client

# ─── MongoTeamManager ────────────────────────────────────────────────────────
class MongoTeamManager:
    def __init__(self):
        self.client = _get_mongo_client()
        
        db_name = get_env("MONGO_DB")
        self.db = self.client[db_name]

        coll_name = get_env("MONGO_COLLECTION")
        self.collection = self.db[coll_name]

    def save_team(self, name: str, abbreviation: str) -> None:
        name_clean  = name.strip().upper()
        abbr_clean  = abbreviation.strip().upper()

        result = self.collection.update_one(
            {"name": name_clean},
            {"$set": {"abbreviation": abbr_clean}},
            upsert=True
        )
        
        # Invalidate cache on write
        global _teams_cache, _teams_cache_timestamp
        with _mongo_client_lock:
            _teams_cache.clear()
            _teams_cache_timestamp = 0
        
        if result.upserted_id:
            print(f"✅ Inserted new team: {name_clean} -> {abbr_clean}")
        else:
            print(f"🔁 Updated team: {name_clean} -> {abbr_clean}")

    def load_teams(self) -> dict[str, str]:
        global _teams_cache, _teams_cache_timestamp
        
        current_time = time.time()
        
        # Check cache first
        with _mongo_client_lock:
            if _teams_cache and (current_time - _teams_cache_timestamp) < _cache_ttl:
                print("🔁 Teams Loaded (cached)")
                return _teams_cache.copy()
        
        # Load from database with projection for better performance
        try:
            teams = {
                doc["name"]: doc["abbreviation"]
                for doc in self.collection.find(projection={"name": 1, "abbreviation": 1, "_id": 0})
            }
            
            # Update cache
            with _mongo_client_lock:
                _teams_cache = teams
                _teams_cache_timestamp = current_time
            
            print("🔁 Teams Loaded (fresh)")
            return teams
            
        except ConnectionFailure as e:
            print(f"❌ MongoDB connection failed: {e}")
            # Return cached data if available, even if expired
            with _mongo_client_lock:
                if _teams_cache:
                    print("🔁 Teams Loaded (stale cache)")
                    return _teams_cache.copy()
            return {}

    def get_abbreviation(self, name: str) -> str:
        name_clean = name.strip().upper()
        
        # Try cache first
        global _teams_cache
        with _mongo_client_lock:
            if name_clean in _teams_cache:
                return _teams_cache[name_clean]
        
        # Fallback to database query
        try:
            doc = self.collection.find_one(
                {"name": name_clean}, 
                projection={"abbreviation": 1, "_id": 0}
            )
            return doc["abbreviation"] if doc else ""
        except ConnectionFailure:
            return ""

    def get_all_names(self) -> list[str]:
        # Use cached data if available
        global _teams_cache
        with _mongo_client_lock:
            if _teams_cache:
                return list(_teams_cache.keys())
        
        # Fallback to database
        try:
            return [doc["name"] for doc in self.collection.find(projection=["name"])]
        except ConnectionFailure:
            return []

    def delete_team(self, name: str) -> bool:
        result = self.collection.delete_one({"name": name.strip().upper()})
        
        # Invalidate cache on delete
        global _teams_cache, _teams_cache_timestamp
        with _mongo_client_lock:
            _teams_cache.clear()
            _teams_cache_timestamp = 0
        
        return result.deleted_count > 0

    def backup_to_json(self) -> None:
        teams = self.load_teams()
        print("**Teams Backed Up**")
        save_teams_to_json(teams)
        
        show_message_notification(
            f"✅ Backup realizado",
            f" Equipas salvas em JSON.",
            icon='✅', bg_color='green'
        )