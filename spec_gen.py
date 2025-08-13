#!/usr/bin/env python3
# spec_gen.py — writes goal_score.spec from easy-to-edit variables
from pathlib import Path

# ── CONFIG (edit here) ──────────────────────────────────────────────────────────
CONFIG = {
    "spec_filename": "goal_score.spec",
    "app_name": "goal_score",
    "entry_script": "src/goal_score.py",
    "icon_path": "src/ui/icons/icon_soft.ico",
    "version_file": "version.txt",

    # Hidden imports actually needed
    "hidden_imports": [
        "customtkinter", 
        "ctkmessagebox",
        "src",
        "src.core",
        "src.ui", 
        "src.utils",
        "src.notification",
        "src.licensing",
        "src.config"
    ],

    # Exclude modules you do NOT use (you confirmed these are safe)
    "excludes": [
        "unittest", "pydoc_data", "test", "lib2to3",
        "idlelib", "turtledemo",
        "html",
        "sqlite3",
        "tkinter.test", "tkinter.tests",
    ],

    # Data to embed
    "datas": [
        (".env.enc", "."),
        ("secret.key", "."),
        ("src/ui/icons", "src/ui/icons"),
    ],

    # Tk/Tcl pruning (keeps only EN/PT msg catalogs & drops demos)
    "prune_tk_msgs": True,
    "keep_tk_langs": ["en", "en_US", "pt", "pt_PT"],
    "drop_tk_demos": True,

    # Tcl encodings pruning (you approved minimal set)
    "prune_tcl_encodings": True,
    "keep_tcl_encodings": [
        "ascii.enc", "cp1252.enc", "utf-8.enc", "utf-16.enc",
        "iso8859-1.enc", "iso8859-15.enc"
    ],

    # Build profiles (dev=onedir; release=onefile+optimize=2)
    "use_icon_in_dev": False,
    "use_version_in_dev": False,
    "optimize_level_release": 2,
    "console": False,  # windowed app

    # UPX compression
    "enable_upx_in_dev": False,
    "enable_upx_in_release": True,
    "upx_dir": r"C:\Tools\upx",   # confirmed path
    "upx_python_dll": False,      # you chose NOT to compress python*.dll

    # Always exclude these from UPX
    "upx_exclude_base": ["python*.dll", "vcruntime*.dll", "ucrtbase.dll"],
}
# ────────────────────────────────────────────────────────────────────────────────

def py_list_str(items): return "[" + ", ".join(repr(i) for i in items) + "]"
def py_tuple_list_str(items): return "[" + ", ".join(f"({repr(a)}, {repr(b)})" for a, b in items) + "]"

def make_spec(cfg: dict) -> str:
    app, entry, icon, ver = cfg["app_name"], cfg["entry_script"], cfg["icon_path"], cfg["version_file"]
    hidden, excludes, datas = py_list_str(cfg["hidden_imports"]), py_list_str(cfg["excludes"]), py_tuple_list_str(cfg["datas"])
    keep_langs, keep_enc = py_list_str(cfg["keep_tk_langs"]), py_list_str(cfg["keep_tcl_encodings"])
    upx_dir = cfg.get("upx_dir") or ""
    upx_exclude = py_list_str(cfg["upx_exclude_base"])

    prune_msgs_block = f"""
# --- Prune Tk/Tcl message catalogs + demos ---
def _prune_tk_msgs(items):
    keep_langs = set({keep_langs})
    out = []
    for src, dest, typecode in items:
        low = src.replace('\\\\', '/').lower()
        if '/tcl/msgs/' in low:
            lang = os.path.basename(low).split('.')[0]
            if lang not in keep_langs:
                continue
        {'if "/tk/demos/" in low: continue' if cfg['drop_tk_demos'] else ''}
        out.append((src, dest, typecode))
    return out

a.datas = _prune_tk_msgs(a.datas)
""".rstrip() if cfg["prune_tk_msgs"] else ""

    prune_enc_block = f"""
# --- Prune Tcl encodings (KEEP ONLY a minimal set) ---
def _prune_tcl_encodings(items):
    keep = set({keep_enc})
    out = []
    for src, dest, typecode in items:
        low = src.replace('\\\\', '/').lower()
        if '/tcl/encoding/' in low:
            if os.path.basename(low) not in keep:
                continue
        out.append((src, dest, typecode))
    return out

a.datas = _prune_tcl_encodings(a.datas)
""".rstrip() if cfg["prune_tcl_encodings"] else ""

    return f"""# {cfg['spec_filename']}
# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Ensure UPX is found
UPX_DIR = {upx_dir!r}
if UPX_DIR:
    os.environ["PATH"] = (UPX_DIR + ";" + os.environ.get("PATH", "")) if os.name == "nt" else (UPX_DIR + ":" + os.environ.get("PATH", ""))

# Toggle with: $env:BUILD_PROFILE='dev' or 'release' (default: release)
PROFILE = os.environ.get("BUILD_PROFILE", "release").lower()
IS_DEV = PROFILE == "dev"

block_cipher = None

ENTRY = {entry!r}
ICON  = {icon!r} if (not IS_DEV or {str(CONFIG["use_icon_in_dev"])}) else None
VER   = {ver!r}  if (not IS_DEV or {str(CONFIG["use_version_in_dev"])}) else None

hiddenimports = {hidden}
excludes = {excludes}
datas = {datas}

a = Analysis(
    [ENTRY],
    pathex=[str(Path('.').resolve())],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    excludes=excludes,
    noarchive=False,
)

# Optimize=0 in dev; {CONFIG["optimize_level_release"]} in release
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher, optimize=(0 if IS_DEV else {CONFIG["optimize_level_release"]}))

{prune_msgs_block}

{prune_enc_block}

exe_kwargs = dict(
    name={app!r},
    icon=ICON,
    debug=IS_DEV,
    strip=not IS_DEV,  # harmless on Windows
    upx=({str(CONFIG["enable_upx_in_dev"])} if IS_DEV else {str(CONFIG["enable_upx_in_release"])}),
    upx_exclude={upx_exclude},
    console={str(CONFIG["console"])},
    disable_windowed_traceback=False,  # Always enable tracebacks for debugging
    version=VER,
)

if IS_DEV:
    exe = EXE(pyz, a.scripts, [], [], [], **exe_kwargs)
    coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas,
                   strip=not IS_DEV, upx=({str(CONFIG["enable_upx_in_dev"])}), name={app!r})
else:
    exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, **exe_kwargs)
"""

def main():
    spec_path = Path(CONFIG["spec_filename"])
    spec_path.write_text(make_spec(CONFIG), encoding="utf-8")
    print(f"Wrote {spec_path.resolve()}")

if __name__ == "__main__":
    main()
