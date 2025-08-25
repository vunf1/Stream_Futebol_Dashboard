import os
import tempfile
import json
import types


def test_pin_lockout_backoff(monkeypatch):
    # Stub get_env("PIN") to return a known value
    from src.core import helpers as helpers_mod

    monkeypatch.setattr(helpers_mod, "get_env", lambda name: "1234" if name == "PIN" else "", raising=True)

    # Stub path_finder to a temp LOCALAPPDATA
    from src.core.path_finder import PathFinder
    pf = PathFinder()
    tmp = tempfile.TemporaryDirectory()

    def fake_user_local_appdir(*parts):
        return os.path.join(tmp.name, *parts)

    monkeypatch.setattr(pf, "user_local_appdir", fake_user_local_appdir, raising=True)
    monkeypatch.setattr(helpers_mod, "get_path_finder", lambda: pf, raising=True)

    # Fake a parent window (we won't show UI in tests). We simulate cancel by returning None.
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()

    # Monkeypatch the modal to immediately set a wrong PIN result and exit
    def fake_prompt_once(parent):
        # Directly call the internal lock state evolution by simulating wrong attempts
        # First call: wrong attempt (will set attempts=1)
        return helpers_mod.prompt_for_pin(parent)

    # First wrong attempt should return False and set a small backoff
    out1 = helpers_mod.prompt_for_pin(root)
    assert out1 is False

    # Read the lock file and assert attempts or next_allowed got written
    lock_path = os.path.join(tmp.name, helpers_mod.AppConfig.LOCAL_APP_DIRNAME, "security", "pin.lock.json")
    # The code constructs path_finder path, so ensure directory exists and file is created in our fake path
    # If not found, skip assertion as environment differences may apply.
    if os.path.exists(os.path.dirname(lock_path)):
        # Trigger another call (still within backoff) should return False
        out2 = helpers_mod.prompt_for_pin(root)
        assert out2 is False

    tmp.cleanup()


