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
from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse
import uvicorn

# 1. Configure Reflex environment
os.environ["REFLEX_ENV_MODE"] = "prod"
os.environ["REFLEX_MOUNT_FRONTEND_COMPILED_APP"] = "False"

# 2. Import the Reflex application
import temis_web.temis_web as temis_app
app_instance = temis_app.app

# 3. Setup Reflex State and Endpoints
from reflex_components_core.core.upload import Upload, get_upload_dir
from reflex._upload import upload, UploadedFilesHeadersMiddleware

Upload.is_used = True
app_instance._setup_state()
app_instance._add_default_endpoints()
app_instance._add_optional_endpoints()

# Guarantee /_upload endpoint is registered explicitly on Starlette app
upload_dir = get_upload_dir()
os.makedirs(upload_dir, exist_ok=True)
has_upload = any(getattr(r, "path", None) == "/_upload" for r in app_instance._api.routes)
if not has_upload:
    app_instance._api.add_route("/_upload", upload(app_instance), methods=["POST"])
    app_instance._api.mount("/_upload", UploadedFilesHeadersMiddleware(StaticFiles(directory=upload_dir)), name="uploaded_files")
print(f"[TEMIS Production Server] Upload endpoints ready. Registered routes: {[getattr(r, 'path', str(r)) for r in app_instance._api.routes]}")


# 4. Locate compiled static client directory
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

    app_instance._api.mount("/", SPAStaticFiles(directory=str(client_dir), html=True), name="frontend")
    print(f"[TEMIS Production Server] Mounted static client from: {client_dir}")
else:
    print(f"[TEMIS Production Server] Warning: Client directory not found at {client_dir}")

# 5. Build Top-Level Starlette ASGI application with Reflex Lifespan and Context Middleware
asgi_app = Starlette(lifespan=app_instance._run_lifespan_tasks)
asgi_app.mount("", app_instance._context_middleware(app_instance._api))
app_instance._add_cors(asgi_app)

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
