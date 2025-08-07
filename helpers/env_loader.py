import os
import sys
from pathlib import Path
from io import StringIO

from cryptography.fernet import Fernet
from dotenv import load_dotenv

class SecureEnvLoader:
    """
    Decrypts an encrypted .env file (using a Fernet key) and loads the
    resulting variables into os.environ via python-dotenv.
    Works both in development and when bundled with PyInstaller (_MEIPASS).
    """
    def __init__(
        self,
        enc_env_filename: str = "../.env.enc",
        key_filename: str = "../secret.key",
        meipass_attr: str = "_MEIPASS"
    ):
        # Determine base path (handles PyInstaller or plain script)
        base = getattr(sys, meipass_attr, None)
        if not base:
            base = Path(__file__).resolve().parent
        else:
            base = Path(base)
        self._key_path = base / key_filename
        self._enc_env_path = base / enc_env_filename

        # Load and cache the Fernet instance
        key_bytes = self._key_path.read_bytes()
        self._fernet = Fernet(key_bytes)

    def load(self) -> None:
        """
        Decrypts the .env file and loads its contents into os.environ.
        """
        encrypted = self._enc_env_path.read_bytes()
        decrypted_text = self._fernet.decrypt(encrypted).decode("utf-8")
        load_dotenv(stream=StringIO(decrypted_text))
        self._wipe()
        
    def _wipe(self):
        # zero out sensitive attributes
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
