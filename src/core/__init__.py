"""
Core utilities for the Stream Futebol Dashboard application.

This module contains essential utilities, configuration management,
and core database functionality.
"""

from .config_manager import ConfigManager, get_config
from .env_loader import SecureEnvLoader
from .filenames import get_env
from .helpers import save_teams_to_json, load_teams_from_json, prompt_for_pin
from .mongodb import MongoTeamManager, _get_mongo_client
from .gameinfo import GameInfoStore, DEFAULT_FIELD_STATE

__all__ = [
    'ConfigManager',
    'get_config',
    'SecureEnvLoader',
    'get_env',
    'save_teams_to_json',
    'load_teams_from_json',
    'prompt_for_pin',
    'MongoTeamManager',
    'GameInfoStore',
    'DEFAULT_FIELD_STATE',
    '_get_mongo_client',
]
