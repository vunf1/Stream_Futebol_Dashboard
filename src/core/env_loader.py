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
                # Dev run: files live at project root
                # Check if we're already in the project root or need to go up
                current_file = Path(__file__).resolve()
                
                # Check if we're in helpers/core/ subdirectory
                if "helpers" in current_file.parts and "core" in current_file.parts:
                    # We're in helpers/core/, go up 2 levels to project root
                    base = current_file.parents[2]
                else:
                    # We're already in project root or somewhere else
                    # Try current working directory first
                    base = Path.cwd()

        self._key_path = (base / key_filename)
        self._enc_env_path = (base / enc_env_filename)

        # Helpful error if files missing
        if not self._key_path.exists():
            print(f"Warning: Secret key not found at: {self._key_path}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Base path: {base}")
            print(f"Current file: {__file__}")
            print("Attempting to load from current working directory...")
            
            # Try current working directory as fallback
            self._key_path = Path(key_filename)
            self._enc_env_path = Path(enc_env_filename)
            
            if not self._key_path.exists():
                raise FileNotFoundError(
                    f"Secret key not found at: {self._key_path}\n"
                    f"Please ensure {key_filename} exists in the project root directory.\n"
                    f"Current working directory: {os.getcwd()}\n"
                    f"Expected locations:\n"
                    f"  - {base / key_filename}\n"
                    f"  - {Path.cwd() / key_filename}"
                )
        
        if not self._enc_env_path.exists():
            raise FileNotFoundError(
                f"Encrypted env file not found at: {self._enc_env_path}\n"
                f"Please ensure {enc_env_filename} exists in the project root directory."
            )

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
