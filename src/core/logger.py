import logging
import sys
import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict

from src.config.settings import AppConfig

_LOGGING_CONFIGURED: bool = False

_HOME_DIR = str(Path.home())
_HOME_DIR_ALT = os.path.expanduser("~")

_URI_CRED_RE = re.compile(r"(://)([^:/\s]+):([^@/\s]+)@")
_SENSITIVE_KV_RE = re.compile(r"(?i)(pin|password|secret|token|key)\s*[:=]\s*([^\s]+)")


def _redact_string(value: str) -> str:
    try:
        if not isinstance(value, str):
            return value
        redacted = value
        # Mask home directory path in any file path string
        if _HOME_DIR:
            redacted = redacted.replace(_HOME_DIR, "~")
        if _HOME_DIR_ALT and _HOME_DIR_ALT != _HOME_DIR:
            redacted = redacted.replace(_HOME_DIR_ALT, "~")
        # Mask credentials in URIs
        redacted = _URI_CRED_RE.sub(r"\1***:***@", redacted)
        # Mask obvious key/value secrets in messages
        redacted = _SENSITIVE_KV_RE.sub(lambda m: f"{m.group(1)}: ***", redacted)
        return redacted
    except Exception:
        return value


class _RedactionFilter(logging.Filter):
    SENSITIVE_KEYS = {"pin", "password", "secret", "token", "apikey", "api_key", "private_key"}

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        try:
            # Redact message
            if isinstance(record.msg, str):
                record.msg = _redact_string(record.msg)
            # Redact extra fields
            for key, val in list(record.__dict__.items()):
                if key in self.SENSITIVE_KEYS:
                    record.__dict__[key] = "***"
                elif isinstance(val, str):
                    record.__dict__[key] = _redact_string(val)
        except Exception:
            pass
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "lvl": record.levelname,  # alias for easy filtering
            "name": record.name,
            "msg": record.getMessage(),
        }

        # Attach extra fields (exclude standard logging attributes)
        standard = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "asctime",
        }
        for key, value in record.__dict__.items():
            if key in standard or key.startswith("_") or key in payload:
                continue
            try:
                json.dumps(value)  # ensure serializable
                payload[key] = value
            except Exception:
                payload[key] = str(value)

        if record.exc_info:
            try:
                payload["exc_info"] = self.formatException(record.exc_info)
            except Exception:
                payload["exc_info"] = "<unserializable exc_info>"

        return json.dumps(payload, ensure_ascii=False)


class _DevFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        ts = datetime.now().strftime("%H:%M:%S")
        # Prefix with explicit level tag for quick scanning
        base = f"[{record.levelname}] [{ts}] {record.name}: {record.getMessage()}"
        if record.exc_info:
            try:
                base += "\n" + self.formatException(record.exc_info)
            except Exception:
                pass
        return base


def _level_from_string(level_str: str) -> int:
    mapping = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }
    return mapping.get(level_str.upper(), logging.INFO)


def setup_logging() -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    root = logging.getLogger()
    root.setLevel(_level_from_string(getattr(AppConfig, "LOG_LEVEL", "INFO")))

    # Avoid duplicate handlers if re-imported
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    if getattr(AppConfig, "DEBUG_MODE", False):
        handler.setFormatter(_DevFormatter())
    else:
        handler.setFormatter(_JsonFormatter())
    # Add redaction filter
    handler.addFilter(_RedactionFilter())
    root.addHandler(handler)

    _LOGGING_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)


