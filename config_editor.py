#!/usr/bin/env python3
"""
Configuration Editor Launcher for Stream Futebol Dashboard
Run this script to open the configuration editor interface.
"""

import sys
import os

# Add the current directory to Python path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.config import show_config_editor
    import customtkinter as ctk
    
    # Set appearance mode
    ctk.set_appearance_mode("dark")
    
    print("Opening Configuration Editor...")
    show_config_editor()
    
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure all dependencies are installed.")
    sys.exit(1)
except Exception as e:
    print(f"Error launching configuration editor: {e}")
    sys.exit(1)
