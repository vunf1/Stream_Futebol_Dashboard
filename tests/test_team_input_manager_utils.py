import threading
import time


def test_team_input_manager_instantiation(monkeypatch):
    # Import lazily to avoid initializing Tk in this test environment
    from src.ui.teamsUI.teams_ui import TeamInputManager
    try:
        import customtkinter as ctk
        root = ctk.CTk()
        # Create minimal mongo/json stubs
        class Mongo:
            def load_teams(self):
                return {"A": "AA"}
        class Store:
            def get(self, *a, **k):
                return ""
        tim = TeamInputManager(root, Mongo(), lambda: None, 1, Store())
        assert tim.instance_number == 1
    finally:
        try:
            root.destroy()
        except Exception:
            pass


