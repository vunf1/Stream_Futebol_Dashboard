import os
from typing import Dict

# Global flag to track if environment has been loaded
_env_loaded = False

def _ensure_env_loaded():
    """Ensure environment variables are loaded before using them"""
    global _env_loaded
    if not _env_loaded:
        try:
            from .env_loader import ensure_env_loaded
            ensure_env_loaded()
            _env_loaded = True
        except Exception as e:
            print(f"Warning: Could not load environment: {e}")
            # Continue anyway, environment variables might be set by other means

def get_env(name: str) -> str:
    """
    Fetches an environment variable or raises if it's not defined.
    Ensures environment is loaded first.
    """
    _ensure_env_loaded()
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Environment variable {name} is not set")
    return value

# Full path to the FUTEBOL-SCORE-DASHBOARD folder on the Desktop
BASE_FOLDER_PATH = os.path.join(
    os.path.expanduser("~"),
    "Desktop",
    "FUTEBOL-SCORE-DASHBOARD"
)

# Map logical keys → file‑stems (no extension)
BASE_FILE_STEMS: Dict[str, str] = {
    'half':        'half',
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
    Returns the full folder path for a given field instance under the base FUTEBOL-SCORE-DASHBOARD folder.

    :param instance_number: numeric ID of the field (e.g. 1, 2, …)
    :return: absolute path to the folder
    """
    folder = os.path.join(
        BASE_FOLDER_PATH,
        f"Campo_{instance_number}"
    )    
    os.makedirs(folder, exist_ok=True)
    return folder


def get_file_path(instance_number: int, key: str, ext: str = ".txt") -> str:
    """
    Returns the full path to the file for `key` under
    FUTEBOL-SCORE-DASHBOARD/Campo_<instance_number> on the Desktop.

    :param instance_number: numeric ID of the field
    :param key: one of the keys in BASE_FILE_STEMS
    :param ext: file extension (defaults to ".txt")
    """

    base_key = key.removesuffix(ext) if key.endswith(ext) else key
    if base_key not in BASE_FILE_STEMS:
        valid = ', '.join(BASE_FILE_STEMS.keys())
        raise KeyError(f'Unknown key {key!r}. Valid keys are: {valid}')
    stem = BASE_FILE_STEMS[base_key]
    folder = get_folder_path(instance_number)
    full_path = os.path.join(folder, f'{stem}{ext}')
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
    base_key = key.removesuffix(ext) if key.endswith(ext) else key
    if base_key not in BASE_FILE_STEMS:
        valid = ', '.join(BASE_FILE_STEMS.keys())
        raise KeyError(f'Unknown key {key!r}. Valid keys are: {valid}')
    stem = BASE_FILE_STEMS[base_key]
    folder = get_folder_path(instance_number)
    full_path = os.path.join(folder, f'{stem}{ext}')

    print(f'🔍 Reading Field {instance_number} - {stem}{ext} (default={default})')
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
            if text:
                return text
            else:
                print(f'⚠️ Field {instance_number} - {stem}{ext} file is empty; writing and returning default={default}')
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(default)
                return default
    except FileNotFoundError:
        print(f'⚠️ Field {instance_number} - {stem}{ext} file not found; creating with default={default}')
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(default)
        except Exception as e:
            print(f'❌ Error creating default file {full_path}: {e}')
        return default
    except UnicodeDecodeError as e:
        print(f'⚠️ Field {instance_number} - {stem}{ext} encoding error: {e}; writing and returning default={default}')
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(default)
        except Exception as e2:
            print(f'❌ Error writing default after decode error {full_path}: {e2}')
        return default
    except Exception as e:
        print(f'❌ Error reading {full_path}: {e}; writing and returning default={default}')
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(default)
        except Exception as e2:
            print(f'❌ Error writing default after general error {full_path}: {e2}')
        return default
