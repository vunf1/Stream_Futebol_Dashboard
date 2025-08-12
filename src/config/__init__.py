"""
Configuration package for Stream Futebol Dashboard.
"""

from .settings import AppConfig
from .config_editor import ConfigEditor, show_config_editor

__all__ = ['AppConfig', 'ConfigEditor', 'show_config_editor']
