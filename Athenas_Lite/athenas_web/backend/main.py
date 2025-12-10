"""
FastAPI main application entry point for ATHENAS Lite Web
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="ATHENAS Lite API",
    description="Audio analysis API with Gemini AI integration",
    version="1.0.0"
)

# CORS configuration
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "ATHENAS Lite API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Import and include routers
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from api import auth, admin, analysis, users, api_keys
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(api_keys.router, prefix="/api/keys", tags=["api-keys"])

# Startup event to initialize database
from services import storage

@app.on_event("startup")
async def startup_event():
    """Initialize database and run migrations on startup"""
    await storage.storage_service.init_database()
    print("✅ Database initialized")
    
    # Run migrations
    import aiosqlite
    from pathlib import Path
    
    migration_file = Path(__file__).parent / "migrations" / "001_add_api_keys.sql"
    if migration_file.exists():
        try:
            async with aiosqlite.connect(storage.storage_service.db_path) as db:
                with open(migration_file, "r") as f:
                    migration_sql = f.read()
                await db.executescript(migration_sql)
                await db.commit()
            print("✅ API keys migration applied")
        except Exception as e:
            print(f"⚠️ Migration warning (may already be applied): {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
