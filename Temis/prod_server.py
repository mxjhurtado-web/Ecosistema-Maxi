#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Production ASGI Server for TEMIS Web Flow on Render.
Serves both the compiled SPA frontend and the Reflex/Starlette WebSocket/REST backend
on a single unified port ($PORT) with minimal memory footprint (<50MB RAM).
"""

import os
import sys
from pathlib import Path
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse
import uvicorn

# 1. Configure Reflex environment
os.environ["REFLEX_ENV_MODE"] = "prod"
os.environ["REFLEX_MOUNT_FRONTEND_COMPILED_APP"] = "True"

# 2. Import the Reflex application
import temis_web.temis_web as temis_app
asgi_app = temis_app.app._api

# 3. Locate compiled static client directory
root_dir = Path(__file__).parent.resolve()
client_dir = root_dir / ".web" / "build" / "client"

if not client_dir.exists():
    alt_client = root_dir / ".web" / "_static"
    if alt_client.exists():
        client_dir = alt_client

if client_dir.exists():
    index_file = client_dir / "index.html"
    
    class SPAStaticFiles(StaticFiles):
        async def get_response(self, path: str, scope):
            response = await super().get_response(path, scope)
            if response.status_code == 404 and index_file.exists():
                return FileResponse(index_file)
            return response

    asgi_app.mount("/", SPAStaticFiles(directory=str(client_dir), html=True), name="frontend")
    print(f"[TEMIS Production Server] Mounted static client from: {client_dir}")
else:
    print(f"[TEMIS Production Server] Warning: Client directory not found at {client_dir}")

def get_app():
    return asgi_app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"[TEMIS Production Server] Starting Uvicorn on {host}:{port}")
    uvicorn.run(
        "prod_server:asgi_app",
        host=host,
        port=port,
        log_level="info",
        access_log=False,
    )
