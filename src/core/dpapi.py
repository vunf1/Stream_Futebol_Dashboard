"""
Windows DPAPI helpers using ctypes.

What this is:
- Lightweight wrappers over Windows Data Protection API to protect/unprotect small
  blobs of secret data (e.g., encryption keys) bound to the current user profile.
- No external dependencies; works on Windows only.

Why it exists:
- Storing a raw Fernet key on disk lets anyone decrypt your encrypted .env file
  if they get file access. DPAPI protects that key at rest by tying it to the
  Windows user account, making offline theft of the key ineffective.

Usage model:
- dpapi_protect(plaintext)  -> ciphertext (store on disk)
- dpapi_unprotect(ciphertext) -> plaintext (use in memory only)
"""

import ctypes
from ctypes import wintypes


class _DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


_crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_CryptProtectData = _crypt32.CryptProtectData
_CryptProtectData.argtypes = [ctypes.POINTER(_DATA_BLOB), wintypes.LPCWSTR, ctypes.POINTER(_DATA_BLOB),
                              wintypes.LPVOID, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(_DATA_BLOB)]
_CryptProtectData.restype = wintypes.BOOL

_CryptUnprotectData = _crypt32.CryptUnprotectData
_CryptUnprotectData.argtypes = [ctypes.POINTER(_DATA_BLOB), ctypes.POINTER(wintypes.LPWSTR), ctypes.POINTER(_DATA_BLOB),
                                wintypes.LPVOID, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(_DATA_BLOB)]
_CryptUnprotectData.restype = wintypes.BOOL

_LocalFree = _kernel32.LocalFree
_LocalFree.argtypes = [wintypes.HLOCAL]
_LocalFree.restype = wintypes.HLOCAL


def _bytes_to_blob(data: bytes) -> _DATA_BLOB:
    buf = (ctypes.c_byte * len(data))(*data)
    return _DATA_BLOB(len(data), buf)


def _blob_to_bytes(blob: _DATA_BLOB) -> bytes:
    cb = int(blob.cbData)
    if cb == 0 or not blob.pbData:
        return b""
    ptr = ctypes.cast(blob.pbData, ctypes.POINTER(ctypes.c_char))
    try:
        return ctypes.string_at(ptr, cb)
    finally:
        _LocalFree(blob.pbData)


def dpapi_protect(plaintext: bytes) -> bytes:
    """Protect data with DPAPI (Current User scope)."""
    in_blob = _bytes_to_blob(plaintext)
    out_blob = _DATA_BLOB()
    if not _CryptProtectData(ctypes.byref(in_blob), None, None, None, None, 0x00, ctypes.byref(out_blob)):
        raise ctypes.WinError(ctypes.get_last_error())
    return _blob_to_bytes(out_blob)


def dpapi_unprotect(ciphertext: bytes) -> bytes:
    """Unprotect data with DPAPI (Current User scope)."""
    in_blob = _bytes_to_blob(ciphertext)
    out_blob = _DATA_BLOB()
    if not _CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0x00, ctypes.byref(out_blob)):
        raise ctypes.WinError(ctypes.get_last_error())
    return _blob_to_bytes(out_blob)


