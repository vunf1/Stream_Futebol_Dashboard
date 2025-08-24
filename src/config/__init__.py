"""
Configuration package for Stream Futebol Dashboard.
"""

from .settings import AppConfig

# Avoid importing ConfigEditor at module import time to prevent circular imports
# If needed elsewhere, import on demand: from src.config.config_editor import ConfigEditor

__all__ = ['AppConfig']
