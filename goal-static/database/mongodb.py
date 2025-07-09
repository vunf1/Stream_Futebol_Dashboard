from pymongo import MongoClient
import os

from helpers.env_loader import EncryptedEnvLoader
# ─── Decrypt & load ─────────────────────────────────────────
EncryptedEnvLoader().load()


_client: MongoClient | None = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(os.getenv("MONGO_URI"))
    return _client


# ─── MongoTeamManager ────────────────────────────────────────────────────────
class MongoTeamManager:
    def __init__(self):
        self.client          = get_client()
        self.db              = self.client[os.getenv("MONGO_DB")]
        self.collection      = self.db[os.getenv("MONGO_COLLECTION")]
        

    def save_team(self, name: str, abbreviation: str) -> None:
        name_clean  = name.strip().upper()
        abbr_clean  = abbreviation.strip().upper()

        result = self.collection.update_one(
            {"name": name_clean},
            {"$set": {"abbreviation": abbr_clean}},
            upsert=True
        )
        if result.upserted_id:
            print(f"✅ Inserted new team: {name_clean} -> {abbr_clean}")
        else:
            print(f"🔁 Updated team: {name_clean} -> {abbr_clean}")

    def load_teams(self) -> dict[str, str]:
        print("🔁 Teams Loaded")
        return {
            doc["name"]: doc["abbreviation"]
            for doc in self.collection.find()
        }

    def get_abbreviation(self, name: str) -> str:
        name_clean = name.strip().upper()
        doc = self.collection.find_one({"name": name_clean})
        return doc["abbreviation"] if doc else ""

    def get_all_names(self) -> list[str]:
        return [doc["name"] for doc in self.collection.find(projection=["name"])]

    def delete_team(self, name: str) -> bool:
        result = self.collection.delete_one({"name": name.strip().upper()})
        return result.deleted_count > 0
