"""
Startup script to set Python path before importing main app
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Add athenas_lite to path for shared modules  
athenas_lite_dir = backend_dir.parent.parent / "athenas_lite"
sys.path.insert(0, str(athenas_lite_dir))

# Now import the app
from main import app

__all__ = ["app"]
