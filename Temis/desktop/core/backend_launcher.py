#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Backend Launcher for TEMIS
Handles automatic backend startup and shutdown
"""

import sys
import os
import subprocess
import time
import requests
import atexit
from pathlib import Path

# Backend process global
_backend_process = None

def start_backend():
    """Start the FastAPI backend server"""
    global _backend_process
    
    try:
        # Check if backend is already running
        try:
            response = requests.get("http://localhost:8000/docs", timeout=2)
            if response.status_code == 200:
                print("[TEMIS] Backend ya está corriendo")
                return True
        except:
            pass
        
        print("[TEMIS] Iniciando backend...")
        
        # Get project root
        if getattr(sys, 'frozen', False):
            # Running as executable
            project_root = Path(sys.executable).parent
        else:
            # Running from source
            project_root = Path(__file__).parent.parent
        
        # Start backend as subprocess
        backend_cmd = [
            sys.executable,
            "-m", "uvicorn",
            "backend.main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--log-level", "error"
        ]
        
        # Create process with no window
        startupinfo = None
        if sys.platform == 'win32':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        _backend_process = subprocess.Popen(
            backend_cmd,
            cwd=str(project_root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )
        
        # Wait for backend to be ready
        print("[TEMIS] Esperando que el backend inicie...")
        for i in range(30):
            try:
                response = requests.get("http://localhost:8000/docs", timeout=1)
                if response.status_code == 200:
                    print("[TEMIS] ✓ Backend iniciado correctamente")
                    # Register cleanup on exit
                    atexit.register(stop_backend)
                    return True
            except:
                time.sleep(1)
        
        print("[TEMIS] ⚠ Backend tardó demasiado en iniciar")
        return False
        
    except Exception as e:
        print(f"[TEMIS] ✗ Error iniciando backend: {e}")
        import traceback
        traceback.print_exc()
        return False

def stop_backend():
    """Stop the backend server"""
    global _backend_process
    
    if _backend_process:
        try:
            print("[TEMIS] Deteniendo backend...")
            _backend_process.terminate()
            
            # Wait for graceful shutdown
            try:
                _backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop
                _backend_process.kill()
                _backend_process.wait()
            
            print("[TEMIS] Backend detenido")
        except Exception as e:
            print(f"[TEMIS] Error deteniendo backend: {e}")
        finally:
            _backend_process = None

def is_backend_running():
    """Check if backend is running"""
    try:
        response = requests.get("http://localhost:8000/docs", timeout=2)
        return response.status_code == 200
    except:
        return False
