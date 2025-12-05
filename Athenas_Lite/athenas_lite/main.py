
import sys
import os

# Add parent directory to sys.path to ensure package imports work
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from athenas_lite.ui.main_window import start_app

if __name__ == "__main__":
    start_app()
