"""
GitMedic - Bootstrap Application Hook
Delegates all execution to the CLI module.
"""
import sys
import os

# Ensure src/ is on the path when running directly
sys.path.insert(0, os.path.dirname(__file__))

from backend.cli import main

if __name__ == "__main__":
    main()
