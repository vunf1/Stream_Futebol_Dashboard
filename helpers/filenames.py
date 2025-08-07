import os
from typing import Dict

def get_env(name: str) -> str:
    """
    Fetches an environment variable or raises if it's not defined.
    """
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is not set")
    return value

# Full path to the OBS_MARCADOR_FUTEBOL folder on the Desktop
BASE_FOLDER_PATH = os.path.join(
    os.path.expanduser("~"),
    "Desktop",
    "OBS_MARCADOR_FUTEBOL"
)

# Map logical keys → file‑stems (no extension)
BASE_FILE_STEMS: Dict[str, str] = {
    'half':        'parte',
    'home_score':  'home_score',
    'away_score':  'away_score',
    'home_name':   'home_name',
    'away_name':   'away_name',
    'home_abbr':   'home_abbr',
    'away_abbr':   'away_abbr',
    'max':         'max',
    'timer':       'timer',
    'extra':       'extra',
}

def get_folder_path(instance_number: int) -> str:
    """
    Returns the full folder path for a given field instance under the base OBS_MARCADOR_FUTEBOL folder.

    :param instance_number: numeric ID of the field (e.g. 1, 2, …)
    :return: absolute path to the folder
    """
    folder = os.path.join(
        BASE_FOLDER_PATH,
        f"Campo_{instance_number}"
    )
    return folder


def get_file_path(instance_number: int, key: str, ext: str = ".txt") -> str:
    """
    Returns the full path to the file for `key` under
    OBS_MARCADOR_FUTEBOL/Campo_<instance_number> on the Desktop.

    :param instance_number: numeric ID of the field
    :param key: one of the keys in BASE_FILE_STEMS
    :param ext: file extension (defaults to ".txt")
    """
    base_key = key.removesuffix(ext) if key.endswith(ext) else key
    try:
        stem = BASE_FILE_STEMS[base_key]
    except KeyError:
        valid = ", ".join(BASE_FILE_STEMS.keys())
        raise KeyError(f"Unknown key '{key}'. Valid keys are: {valid}")

    # Build the folder path for this instance
    folder = get_folder_path(instance_number)
    full_path = os.path.join(folder, f"{stem}{ext}")

    return full_path

def get_file_value(
    instance_number: int,
    key: str,
    default: str,
    ext: str = ".txt"
) -> str:
    """
    Combines path resolution + file reading with fallback.
    :param instance_number: numeric ID of the field
    :param key: one of BASE_FILE_STEMS keys, with or without extension
    :param default: value to return if file is missing/empty/error
    :param ext: file extension (defaults to ".txt")
    :raises KeyError: if key is not known
    :return: the file’s text content or default
    """
    # allow "timer" or "timer.txt"
    base_key = key[:-len(ext)] if key.endswith(ext) else key
    try:
        stem = BASE_FILE_STEMS[base_key]
    except KeyError:
        valid = ", ".join(BASE_FILE_STEMS.keys())
        raise KeyError(f"Unknown key '{key}'. Valid keys are: {valid}")

    # build full path
    folder = os.path.join(BASE_FOLDER_PATH, f"Campo_{instance_number}")
    full_path = os.path.join(folder, f"{stem}{ext}")

    print(f"🔍 Reading ' Field {instance_number} - {stem}{ext}' (default='{default}')")
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
            if text:
                return text
            else:
                print(f"⚠️ ' Field {instance_number} - {stem}{ext}' File is empty'; returning default - '{default}'")
                return default
    except FileNotFoundError:
        print(f"⚠️ ' Field {instance_number} - {stem}{ext}' File not found'; returning default - '{default}'")
        return default
    except UnicodeDecodeError as e:
        print(f"⚠️ ' Field {instance_number} - {stem}{ext}' Encoding error': {e}; returning default - '{default}'")
        return default
    except Exception as e:
        print(f"❌ Error reading '{full_path}': {e}; returning default - '{default}'")
        return default