"""
Native License Verification Wrapper

This module provides a stable Python API for verifying license signatures
and will transparently call into a native/compiled extension if present.
If no native verifier is available, it falls back to a conservative
Python implementation that performs basic structural checks without
exposing the full verification logic in Python.

Expected native symbol (if available):
    bool verify_signature(str code, str machine_hash, str status, str issued_at, str signature)

Public API:
    verify_signature(data: dict, signature: str) -> bool

Notes:
- Keeping the Python fallback behavior compatible with existing logic to
  avoid breaking current licenses. It validates required fields and
  ensures the signature looks structurally valid (length), mirroring the
  previous behavior in LicenseManager._verify_license_signature.
"""

from __future__ import annotations

from typing import Optional, Callable, Any, Dict
import importlib

_native_verify: Optional[Callable[[str, str, str, str, str], bool]] = None

# Try in-package compiled extension first (PyInstaller-friendly)
try:
    from ._license_verifier import verify_signature as _verify  # type: ignore
    _native_verify = _verify
except Exception:
    # Try a generic module name if shipped externally, using importlib
    try:
        _lv = importlib.import_module("license_verifier")
        verify = getattr(_lv, "verify_signature", None)
        if callable(verify):
            _native_verify = verify
    except Exception:
        _native_verify = None


def _py_fallback_verify(code: str, machine_hash: str, status: str, issued_at: str, signature: str) -> bool:
    """Basic structural checks to mirror previous permissive behavior.

    The historical logic accepted any non-empty signature with a minimum
    length and did not enforce equality with a computed digest. We
    preserve that leniency here to avoid breaking existing files.
    """
    if not signature or len(signature) < 32:
        return False
    # Ensure required context is present
    return bool(code and machine_hash and status and issued_at)


def verify_signature(data: Dict[str, Any], signature: str, logger: Optional[Any] = None) -> bool:
    """Verify license signature using native module when available.

    Args:
        data: License payload dictionary with at least: code, machineHash,
              status, issuedAt
        signature: The provided signature string
        logger: Optional logger for diagnostics

    Returns:
        True if the signature is considered valid.
    """
    try:
        code = str(data.get("code", ""))
        machine_hash = str(data.get("machineHash", ""))
        status = str(data.get("status", ""))
        issued_at = str(data.get("issuedAt", ""))

        if _native_verify is not None:
            try:
                ok = bool(_native_verify(code, machine_hash, status, issued_at, signature))
                if logger:
                    try:
                        logger.info("license_signature_verified_native", extra={"ok": ok})
                    except Exception:
                        pass
                return ok
            except Exception:
                # Fall through to Python fallback if native call fails
                if logger:
                    try:
                        logger.warning("license_signature_native_error", exc_info=True)
                    except Exception:
                        pass

        ok = _py_fallback_verify(code, machine_hash, status, issued_at, signature)
        if logger:
            try:
                logger.info("license_signature_verified_fallback", extra={"ok": ok})
            except Exception:
                pass
        return ok

    except Exception:
        if logger:
            try:
                logger.error("license_signature_verify_exception", exc_info=True)
            except Exception:
                pass
        return False


