#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TEMIS Backend Standalone Entry Point
Runs the FastAPI backend as a standalone application
"""

if __name__ == "__main__":
    import uvicorn
    import sys
    import os
    from pathlib import Path
    
    # Add project root to path
    if getattr(sys, 'frozen', False):
        # Running as executable
        project_root = Path(sys.executable).parent
    else:
        # Running from source
        project_root = Path(__file__).parent
    
    sys.path.insert(0, str(project_root))
    
    # Import and run the app
    from backend.main import app
    
    print("[TEMIS Backend] Iniciando servidor...")
    print("[TEMIS Backend] URL: http://127.0.0.1:8000")
    print("[TEMIS Backend] Docs: http://127.0.0.1:8000/docs")
    
    # Configure uvicorn to work in executable environment
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_config=None,  # Disable default logging config to avoid TTY errors
        access_log=False   # Disable access log
    )
