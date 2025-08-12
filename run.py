#!/usr/bin/env python3
"""
Launcher script for Stream Futebol Dashboard
Run this script from the root directory to start the application.
"""

import sys
import os

# Add the current directory to Python path so we can import from src
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main function from goal_score
from src.goal_score import main

if __name__ == '__main__':
    main()
