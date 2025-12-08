"""
Database and storage management service
Handles SQLite operations, file management, and user sync
"""
import aiosqlite
import os
import shutil
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

class StorageService:
    """Manages database and file storage operations"""
    
    def __init__(self):
        self.db_path = os.getenv("DATABASE_PATH", "./data/athenas_history.db")
        self.temp_audio_dir = os.getenv("TEMP_AUDIO_DIR", "./temp_audio")
        
        # Ensure directories exist
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.temp_audio_dir).mkdir(parents=True, exist_ok=True)
    
    async def init_database(self):
        """Initialize database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    keycloak_id TEXT UNIQUE NOT NULL,
                    name TEXT,
                    role TEXT NOT NULL,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Departments table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS departments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Rubrics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS rubrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    department_id INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (department_id) REFERENCES departments(id)
                )
            """)
            
            # Analyses table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    department TEXT NOT NULL,
                    evaluator TEXT NOT NULL,
                    advisor TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    score_bruto REAL,
                    score_final REAL,
                    sentiment TEXT,
                    drive_txt_link TEXT,
                    drive_csv_link TEXT,
                    drive_pdf_link TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            await db.commit()
    
    async def sync_user(self, email: str, keycloak_id: str, name: str, role: str = None) -> tuple[int, str]:
        """
        Sync user from Keycloak, create if not exists, return (user_id, role)
        Role assignment:
        - mxjhurtado@maxillc.com is always 'admin' (super admin)
        - Other users default to 'user' unless explicitly set to 'admin' in DB
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Super admin check
            if email == "mxjhurtado@maxillc.com":
                role = 'admin'
            
            # Check if user exists
            async with db.execute(
                "SELECT id, role FROM users WHERE keycloak_id = ?", (keycloak_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    user_id = row[0]
                    existing_role = row[1]
                    
                    # Super admin always stays admin
                    if email == "mxjhurtado@maxillc.com":
                        final_role = 'admin'
                    else:
                        # Keep existing role from DB
                        final_role = existing_role
                    
                    # Update last login and ensure role is correct
                    await db.execute(
                        "UPDATE users SET last_login = ?, role = ?, name = ? WHERE id = ?",
                        (datetime.now(), final_role, name, user_id)
                    )
                else:
                    # Create new user
                    # Super admin gets 'admin', everyone else gets 'user' by default
                    if email == "mxjhurtado@maxillc.com":
                        final_role = 'admin'
                    else:
                        final_role = role if role else 'user'
                    
                    cursor = await db.execute(
                        """INSERT INTO users (email, keycloak_id, name, role, last_login)
                           VALUES (?, ?, ?, ?, ?)""",
                        (email, keycloak_id, name, final_role, datetime.now())
                    )
                    user_id = cursor.lastrowid
                
                await db.commit()
                return user_id, final_role
    
    async def get_departments(self, active_only: bool = True) -> List[Dict]:
        """Get all departments"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM departments"
            if active_only:
                query += " WHERE active = 1"
            query += " ORDER BY name"
            
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def add_department(self, name: str, active: bool = True) -> int:
        """Add new department"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO departments (name, active) VALUES (?, ?)",
                (name, active)
            )
            await db.commit()
            return cursor.lastrowid
    
    async def update_department(self, dept_id: int, name: str, active: bool):
        """Update department"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE departments SET name = ?, active = ? WHERE id = ?",
                (name, active, dept_id)
            )
            await db.commit()
    
    async def delete_department(self, dept_id: int):
        """Delete department"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM departments WHERE id = ?", (dept_id,))
            await db.commit()
    
    async def save_analysis(
        self,
        user_id: int,
        filename: str,
        department: str,
        evaluator: str,
        advisor: str,
        score_bruto: float,
        score_final: float,
        sentiment: str,
        drive_txt_link: Optional[str] = None,
        drive_csv_link: Optional[str] = None,
        drive_pdf_link: Optional[str] = None
    ) -> int:
        """Save analysis result to database"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO analyses 
                   (user_id, filename, department, evaluator, advisor, 
                    score_bruto, score_final, sentiment, 
                    drive_txt_link, drive_csv_link, drive_pdf_link)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, filename, department, evaluator, advisor,
                 score_bruto, score_final, sentiment,
                 drive_txt_link, drive_csv_link, drive_pdf_link)
            )
            await db.commit()
            return cursor.lastrowid
    
    async def get_analyses(
        self,
        user_id: Optional[int] = None,
        department: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get analysis history"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            query = "SELECT * FROM analyses WHERE 1=1"
            params = []
            
            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)
            
            if department:
                query += " AND department = ?"
                params.append(department)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_analysis_by_id(self, analysis_id: int) -> Optional[Dict]:
        """Get single analysis by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    def save_temp_audio(self, file_content: bytes, filename: str) -> str:
        """Save uploaded audio file temporarily"""
        filepath = os.path.join(self.temp_audio_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(file_content)
        return filepath
    
    def cleanup_temp_audio(self, filepath: str):
        """Delete temporary audio file"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Error cleaning up {filepath}: {e}")
    
    def cleanup_old_temp_files(self, max_age_minutes: int = 60):
        """Clean up old temporary files"""
        try:
            now = datetime.now().timestamp()
            for filename in os.listdir(self.temp_audio_dir):
                filepath = os.path.join(self.temp_audio_dir, filename)
                if os.path.isfile(filepath):
                    file_age = now - os.path.getmtime(filepath)
                    if file_age > (max_age_minutes * 60):
                        os.remove(filepath)
        except Exception as e:
            print(f"Error during cleanup: {e}")

# Global instance
storage_service = StorageService()
