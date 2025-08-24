import pytest

from src.core.env_loader import SecureEnvLoader


def test_env_loader_missing_files_raises():
    loader = SecureEnvLoader(enc_env_filename="__nope__.env.enc", key_filename="__nope__.key")
    with pytest.raises(FileNotFoundError):
        loader.load()


