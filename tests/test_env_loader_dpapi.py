import os
import tempfile

import pytest
from cryptography.fernet import Fernet


def _write_files(tmpdir: str, fernet_key: bytes, env_text: str) -> None:
    # Encrypt env text with Fernet key
    f = Fernet(fernet_key)
    encrypted = f.encrypt(env_text.encode("utf-8"))
    # Write .env.enc
    with open(os.path.join(tmpdir, ".env.enc"), "wb") as fh:
        fh.write(encrypted)


def test_secure_env_loader_with_dpapi_key(monkeypatch):
    from src.core import env_loader as env_loader_mod
    from src.core.env_loader import SecureEnvLoader

    with tempfile.TemporaryDirectory() as tmp:
        # Generate a valid Fernet key, but place a non-Fernet blob in secret.key.
        fernet_key = Fernet.generate_key()
        _write_files(tmp, fernet_key, "PIN=123456\n")
        with open(os.path.join(tmp, "secret.key"), "wb") as fh:
            fh.write(b"not-a-valid-fernet-key-bytes")

        # Point loader to our temp dir
        monkeypatch.setenv("GOAL_ENV_DIR", tmp)

        # Monkeypatch dpapi_unprotect to return the real Fernet key
        def fake_unprotect(blob: bytes) -> bytes:
            return fernet_key

        monkeypatch.setattr(env_loader_mod, "dpapi_unprotect", fake_unprotect, raising=True)

        # Ensure PIN not set before
        monkeypatch.delenv("PIN", raising=False)

        loader = SecureEnvLoader()
        loader.load()

        assert os.getenv("PIN") == "123456"

        # Cleanup env
        monkeypatch.delenv("GOAL_ENV_DIR", raising=False)
        monkeypatch.delenv("PIN", raising=False)


def test_secure_env_loader_with_plain_fernet_key(monkeypatch):
    from src.core.env_loader import SecureEnvLoader

    with tempfile.TemporaryDirectory() as tmp:
        fernet_key = Fernet.generate_key()
        _write_files(tmp, fernet_key, "MONGO_DB=testdb\n")
        # Write a valid Fernet key into secret.key
        with open(os.path.join(tmp, "secret.key"), "wb") as fh:
            fh.write(fernet_key)

        monkeypatch.setenv("GOAL_ENV_DIR", tmp)
        monkeypatch.delenv("MONGO_DB", raising=False)

        loader = SecureEnvLoader()
        loader.load()

        assert os.getenv("MONGO_DB") == "testdb"

        # After load, the loader should have hardened the key with DPAPI protection
        # Ensure the file content changed and is not the raw key anymore
        hardened = open(os.path.join(tmp, "secret.key"), "rb").read()
        assert hardened != fernet_key

        monkeypatch.delenv("GOAL_ENV_DIR", raising=False)
        monkeypatch.delenv("MONGO_DB", raising=False)


