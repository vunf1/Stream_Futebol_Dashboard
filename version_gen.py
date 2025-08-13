#!/usr/bin/env python3
from datetime import datetime, timezone

# ──────── Configuration ────────

# 1) Semantic version string
version_str = "11.0.0"
# 2) Parse into a tuple of ints (must be 4-tuple for PyInstaller)
version_tuple = tuple(int(x) for x in version_str.split(".")) + (0,)

# 3) Static fields for this build
company_name       = "Maia Soluções Informáticas"
file_description   = "Sport Tracking for Streaming Services"
internal_name      = "Futebol_Dashboard"
legal_copyright    = "© 2025 Maia Soluções Informáticas"
original_filename  = "Futebol_Dashboard.exe"
product_name       = "Futebol Dashboard"
product_version    = version_str

# (omit Comments, SpecialBuild, etc.)

# 4) Language-codepage for StringTable — 0x0409 is English (US), 1252 is Western
lang_codepage = "040904B0"
translation   = [0x081E, 1252]  # 0x081E == 2070

# ──────── Build the StringStruct block ────────

fields = [
    ("CompanyName",      company_name),
    ("FileDescription",  file_description),
    ("FileVersion",      version_str),
    ("InternalName",     internal_name),
    ("LegalCopyright",   legal_copyright),
    ("OriginalFilename", original_filename),
    ("ProductName",      product_name),
    ("ProductVersion",   product_version),
]

stringstruct_block = ",\n        ".join(
    f"StringStruct('{key}', '{value}')"
    for key, value in fields
)

# ──────── Render the full template ────────

template = f"""# version.txt
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_tuple},
    prodvers={version_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo([
      StringTable(
        '{lang_codepage}',
        [
        {stringstruct_block}
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', {translation})])
  ]
)
"""

# ──────── Write out version.txt ────────

with open("version.txt", "w", encoding="utf-8") as f:
    f.write(template)

print("version.txt generated")
