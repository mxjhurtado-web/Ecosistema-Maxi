"""
Startup script for ATHENAS Web Backend
Runs the backend as a Python module to support relative imports
"""
import sys
from pathlib import Path

# Add athenas_lite to path
backend_dir = Path(__file__).parent
athenas_lite_dir = backend_dir.parent.parent / "athenas_lite"
sys.path.insert(0, str(athenas_lite_dir))

# Now run uvicorn
if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        reload_dirs=[str(backend_dir)]
    )
