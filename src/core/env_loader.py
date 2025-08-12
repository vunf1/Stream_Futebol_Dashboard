import os
import sys
import time
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
        self.enc_env_filename = enc_env_filename
        self.key_filename = key_filename
        self.meipass_attr = meipass_attr
        self.env_dir_envvar = env_dir_envvar
        self._fernet = None
        self._loaded = False

    def _find_files(self):
        """Find the secret key and encrypted env file paths"""
        # Try multiple possible locations in order of preference
        
        # 1. Try PyInstaller _MEIPASS directory first
        base = getattr(sys, self.meipass_attr, None)
        if base:
            key_path = Path(base) / self.key_filename
            enc_env_path = Path(base) / self.enc_env_filename
            if key_path.exists() and enc_env_path.exists():
                return key_path, enc_env_path
        
        # 2. Try explicit override directory
        override_dir = os.getenv(self.env_dir_envvar)
        if override_dir:
            key_path = Path(override_dir) / self.key_filename
            enc_env_path = Path(override_dir) / self.enc_env_filename
            if key_path.exists() and enc_env_path.exists():
                return key_path, enc_env_path
        
        # 3. Try current working directory
        key_path = Path.cwd() / self.key_filename
        enc_env_path = Path.cwd() / self.enc_env_filename
        if key_path.exists() and enc_env_path.exists():
            return key_path, enc_env_path
        
        # 4. Try project root (relative to this file)
        current_file = Path(__file__).resolve()
        if "helpers" in current_file.parts and "core" in current_file.parts:
            # We're in helpers/core/, go up 2 levels to project root
            base = current_file.parents[2]
        else:
            # We're already in project root or somewhere else
            base = current_file.parent
            
        key_path = base / self.key_filename
        enc_env_path = base / self.enc_env_filename
        if key_path.exists() and enc_env_path.exists():
            return key_path, enc_env_path
        
        # 5. Try parent directories (in case we're in a subdirectory)
        for parent in current_file.parents:
            key_path = parent / self.key_filename
            enc_env_path = parent / self.enc_env_filename
            if key_path.exists() and enc_env_path.exists():
                return key_path, enc_env_path
        
        # 6. Try Desktop/FUTEBOL-SCORE-DASHBOARD (common deployment location)
        desktop_path = Path.home() / "Desktop" / "FUTEBOL-SCORE-DASHBOARD"
        key_path = desktop_path / self.key_filename
        enc_env_path = desktop_path / self.enc_env_filename
        if key_path.exists() and enc_env_path.exists():
            return key_path, enc_env_path
            
        # If we get here, we couldn't find the files
        return None, None

    def _wait_for_pyinstaller_init(self, max_retries=20, delay=0.05):
        """Wait for PyInstaller to fully initialize in frozen mode"""
        if not getattr(sys, self.meipass_attr, None):
            return False
            
        for attempt in range(max_retries):
            try:
                base = Path(getattr(sys, self.meipass_attr))
                key_path = base / self.key_filename
                enc_env_path = base / self.enc_env_filename
                
                if key_path.exists() and enc_env_path.exists():
                    return True
                    
                time.sleep(delay)
            except Exception:
                time.sleep(delay)
                
        return False

    def load(self) -> None:
        """Load and decrypt the environment variables"""
        if self._loaded:
            return
            
        # In frozen mode, wait for PyInstaller to fully initialize
        if getattr(sys, self.meipass_attr, None) and not self._wait_for_pyinstaller_init():
            print("Warning: PyInstaller not fully initialized, trying fallback paths...")
            
        key_path, enc_env_path = self._find_files()
        
        # Helpful error if files missing
        if not key_path or not enc_env_path:
            print("Error: Secret key and encrypted env file not found in any expected location.")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Current file: {__file__}")
            print("Searched in the following locations:")
            
            # List all the locations we searched
            locations = []
            
            # PyInstaller _MEIPASS
            base = getattr(sys, self.meipass_attr, None)
            if base:
                locations.append(f"  - PyInstaller temp dir: {base}")
            
            # Override directory
            override_dir = os.getenv(self.env_dir_envvar)
            if override_dir:
                locations.append(f"  - Override dir: {override_dir}")
            
            # Current working directory
            locations.append(f"  - Current working dir: {Path.cwd()}")
            
            # Project root
            current_file = Path(__file__).resolve()
            if "helpers" in current_file.parts and "core" in current_file.parts:
                base = current_file.parents[2]
            else:
                base = current_file.parent
            locations.append(f"  - Project root: {base}")
            
            # Desktop location
            desktop_path = Path.home() / "Desktop" / "FUTEBOL-SCORE-DASHBOARD"
            locations.append(f"  - Desktop location: {desktop_path}")
            
            for loc in locations:
                print(loc)
            
            raise FileNotFoundError(
                f"Secret key and encrypted env file not found.\n"
                f"Please ensure {self.key_filename} and {self.enc_env_filename} exist in one of the expected locations.\n"
                f"Current working directory: {os.getcwd()}"
            )
        
        if not key_path.exists():
            raise FileNotFoundError(
                f"Secret key not found at: {key_path}"
            )
            
        if not enc_env_path.exists():
            raise FileNotFoundError(
                f"Encrypted env file not found at: {enc_env_path}"
            )

        # Prepare Fernet
        key_bytes = key_path.read_bytes()
        self._fernet = Fernet(key_bytes)

        # Load and decrypt
        encrypted = enc_env_path.read_bytes()
        decrypted_text = self._fernet.decrypt(encrypted).decode("utf-8")
        load_dotenv(stream=StringIO(decrypted_text))
        
        print(f"✅ Environment loaded successfully from: {key_path.parent}")
        
        self._loaded = True
        self._wipe()

    def _wipe(self):
        """Clean up sensitive data"""
        if self._fernet:
            del self._fernet
            self._fernet = None

# Global instance for lazy loading
_global_env_loader = None

def get_global_env_loader():
    """Get the global environment loader instance"""
    global _global_env_loader
    if _global_env_loader is None:
        _global_env_loader = SecureEnvLoader()
    return _global_env_loader

def ensure_env_loaded():
    """Ensure environment variables are loaded (lazy loading)"""
    get_global_env_loader().load()

# ──────────────────────────────────────────────────────────────────────────────
# Usage: 
# 
# Option 1: Lazy loading (recommended for PyInstaller)
# from src.core.env_loader import ensure_env_loaded
# ensure_env_loaded()  # Call this when you need env vars
#
# Option 2: Direct usage
# from src.core.env_loader import SecureEnvLoader
# SecureEnvLoader().load()
#
# Then all your subsequent code can safely use os.getenv("MONGO_URI"), etc.
# ──────────────────────────────────────────────────────────────────────────────
