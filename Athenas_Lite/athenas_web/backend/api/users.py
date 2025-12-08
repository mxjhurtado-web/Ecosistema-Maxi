"""
User management endpoints for admins
"""
from fastapi import APIRouter, HTTPException, Depends, Cookie
from typing import Optional, List
from services.storage import storage_service
from services.keycloak import keycloak_service
from models.schemas import UserCreate

router = APIRouter()

async def verify_admin(access_token: Optional[str] = Cookie(None)):
    """Dependency to verify admin role from internal DB"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get user info from Keycloak
    success, user_data = keycloak_service.get_user_info(access_token)
    if not success:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    email = user_data.get("email")
    
    # Check if user is admin in our DB
    user_id, role = await storage_service.sync_user(
        email=email,
        keycloak_id=user_data.get("sub"),
        name=user_data.get("name", user_data.get("preferred_username", ""))
    )
    
    if role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user_id

@router.get("/users")
async def list_users(_: int = Depends(verify_admin)):
    """List all users with their roles"""
    import aiosqlite
    
    async with aiosqlite.connect(storage_service.db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT id, email, name, role, last_login, created_at FROM users ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "email": row["email"],
                    "name": row["name"],
                    "role": row["role"],
                    "last_login": row["last_login"],
                    "created_at": row["created_at"]
                }
                for row in rows
            ]

@router.post("/users")
async def create_user(
    new_user: UserCreate,
    admin_id: int = Depends(verify_admin)
):
    """Create a new user manually (pre-provisioning)"""
    import aiosqlite
    from datetime import datetime
    
    async with aiosqlite.connect(storage_service.db_path) as db:
        # Check if user already exists
        async with db.execute(
            "SELECT id FROM users WHERE email = ?", (new_user.email,)
        ) as cursor:
            if await cursor.fetchone():
                raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create user
        now = datetime.utcnow().isoformat()
        await db.execute(
            """
            INSERT INTO users (email, name, role, created_at, last_login)
            VALUES (?, ?, ?, ?, ?)
            """,
            (new_user.email, new_user.name, new_user.role, now, None)
        )
        await db.commit()
    
    return {"message": "User created successfully"}

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: str,
    admin_id: int = Depends(verify_admin)
):
    """Update user role (admin only)"""
    if new_role not in ['admin', 'user']:
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'")
    
    import aiosqlite
    
    async with aiosqlite.connect(storage_service.db_path) as db:
        # Check if user exists and is not super admin
        async with db.execute(
            "SELECT email FROM users WHERE id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Prevent changing super admin role
            if row[0] == "mxjhurtado@maxillc.com":
                raise HTTPException(status_code=403, detail="Cannot change super admin role")
        
        # Update role
        await db.execute(
            "UPDATE users SET role = ? WHERE id = ?",
            (new_role, user_id)
        )
        await db.commit()
    
    return {"message": f"User role updated to {new_role}"}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin_id: int = Depends(verify_admin)
):
    """Delete user (admin only)"""
    import aiosqlite
    
    async with aiosqlite.connect(storage_service.db_path) as db:
        # Check if user is super admin
        async with db.execute(
            "SELECT email FROM users WHERE id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Prevent deleting super admin
            if row[0] == "mxjhurtado@maxillc.com":
                raise HTTPException(status_code=403, detail="Cannot delete super admin")
        
        # Delete user
        await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await db.commit()
    
    return {"message": "User deleted successfully"}
