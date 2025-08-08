import os
import sys
from pathlib import Path
from io import StringIO

from cryptography.fernet import Fernet
from dotenv import load_dotenv

class SecureEnvLoader:
    """
    Decrypts an encrypted .env file and loads it into os.environ.
    Works both in development and when bundled with PyInstaller (onefile).
    """

    def __init__(
        self,
        enc_env_filename: str = ".env.enc",
        key_filename: str = "secret.key",
        meipass_attr: str = "_MEIPASS",
        env_dir_envvar: str = "GOAL_ENV_DIR",   # optional override
    ):
        # Optional explicit dir via env var (handy for debugging/custom layouts)
        override_dir = os.getenv(env_dir_envvar)
        if override_dir:
            base = Path(override_dir)
        else:
            base = getattr(sys, meipass_attr, None)
            if base:
                # Frozen app: PyInstaller unpacks data into this dir
                base = Path(base)
            else:
                # Dev run: files live at project root (parent of helpers/)
                base = Path(__file__).resolve().parents[1]

        self._key_path = (base / key_filename)
        self._enc_env_path = (base / enc_env_filename)

        # Helpful error if files missing
        if not self._key_path.exists():
            raise FileNotFoundError(f"secret key not found at: {self._key_path}")
        if not self._enc_env_path.exists():
            raise FileNotFoundError(f"encrypted env not found at: {self._enc_env_path}")

        # Prepare Fernet
        key_bytes = self._key_path.read_bytes()
        self._fernet = Fernet(key_bytes)

    def load(self) -> None:
        encrypted = self._enc_env_path.read_bytes()
        decrypted_text = self._fernet.decrypt(encrypted).decode("utf-8")
        load_dotenv(stream=StringIO(decrypted_text))
        self._wipe()

    def _wipe(self):
        del self._fernet

# ──────────────────────────────────────────────────────────────────────────────
# Usage: at the very top of your main module, before any os.getenv() calls:
# 
# from env_loader import SecureEnvLoader
# SecureEnvLoader().load()
#
# Then all your subsequent code (e.g. get_client(), MongoTeamManager, etc.)
# can safely use os.getenv("MONGO_URI"), etc.
# ──────────────────────────────────────────────────────────────────────────────
