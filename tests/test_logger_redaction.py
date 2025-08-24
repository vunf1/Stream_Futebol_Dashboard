import sys
from pathlib import Path

from src.core.logger import get_logger, setup_logging
from src.config.settings import AppConfig


def test_logger_redaction_masks_home_and_secrets(caplog):
    # Force prod formatter (JSON) for stable output
    AppConfig.DEBUG_MODE = False
    setup_logging()
    log = get_logger("test.redaction")
    home = str(Path.home())
    uri = "http://user:pass@host/"
    msg = f"Path: {home} password: supersecret uri={uri}"
    log.info(msg, extra={"pin": "1234"})
    text = caplog.text
    assert "supersecret" not in text
    assert home not in text
    assert "~" in text
    assert "***" in text
    assert "***:***@" in text


