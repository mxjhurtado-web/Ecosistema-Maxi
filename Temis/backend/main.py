#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FastAPI main application for TEMIS
"""

import sys
import os

# Force UTF-8 encoding on Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.database import engine, Base, get_db
from backend.routers import auth, projects, groups, daily_log, eod, phases, members, chat, wizard, shared_db
from backend.models import user, group, project, phase, daily_log as daily_log_model, chat_message

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="TEMIS API",
    description="API for TEMIS Project Management System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(groups.router, prefix="/api/groups", tags=["groups"])
app.include_router(daily_log.router, prefix="/api/daily-log", tags=["daily-log"])
app.include_router(eod.router, prefix="/api/eod", tags=["eod"])
app.include_router(phases.router, prefix="/api/phases", tags=["phases"])
app.include_router(members.router, prefix="/api/members", tags=["members"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(wizard.router)  # Wizard has its own prefix
app.include_router(shared_db.router, prefix="/api/shared-db", tags=["shared-db"])


@app.get("/")
def read_root():
    """Root endpoint"""
    return {"message": "TEMIS API is running"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    print("[INFO] Starting TEMIS Backend Server...")
    print("[INFO] UTF-8 encoding configured for Windows")
    uvicorn.run(app, host="0.0.0.0", port=8000)
