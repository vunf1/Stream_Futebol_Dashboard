from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

class MongoTeamManager:
    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI")
        self.db_name = os.getenv("MONGO_DB")
        self.collection_name = os.getenv("MONGO_COLLECTION")

        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

    def save_team(self, name, abbreviation):
        name = name.upper().strip()
        abbreviation = abbreviation.upper().strip()
        
        existing = self.collection.find_one({"name": name})
        if existing:
            self.collection.update_one({"name": name}, {"$set": {"abbreviation": abbreviation}})
            print(f"🔁 Updated team: {name} -> {abbreviation}")
        else:
            self.collection.insert_one({"name": name, "abbreviation": abbreviation})
            print(f"✅ Inserted new team: {name} -> {abbreviation}")

    def load_teams(self):
        print(f"🔁 Teams Loaded")
        teams = self.collection.find()
        return {team["name"]: team["abbreviation"] for team in teams}

    def get_abbreviation(self, name):
        result = self.collection.find_one({"name": name.upper().strip()})
        if result:
            return result["abbreviation"]
        return ""

    def get_all_names(self):
        return [team["name"] for team in self.collection.find()]

