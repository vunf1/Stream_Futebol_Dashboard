from pymongo import MongoClient
from assets.colors import COLOR_SUCCESS
from helpers.env_loader import SecureEnvLoader
from helpers.filenames import get_env
from helpers.helpers import save_teams_to_json
from helpers.notification.toast import show_message_notification
# ─── Decrypt & load ─────────────────────────────────────────
SecureEnvLoader().load()

# ─── MongoTeamManager ────────────────────────────────────────────────────────
class MongoTeamManager:
    def __init__(self):
        uri = get_env("MONGO_URI")
        self.client = MongoClient(uri)

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

    def backup_to_json(self) -> None:
        teams = self.load_teams()
        print("**Teams Backed Up**")
        save_teams_to_json(teams)
        
        show_message_notification(
            f"✅ Backup realizado",
            f" Equipas salvas em JSON.",
            icon='✅', bg_color=COLOR_SUCCESS
        )