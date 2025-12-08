"""
Admin API endpoints for system management
Protected by admin role verification
"""
from fastapi import APIRouter, HTTPException, Depends, Cookie
from typing import Optional, List
from models.schemas import Department, DepartmentCreate, UserCreate
from services.storage import storage_service
from services.keycloak import keycloak_service

router = APIRouter()

async def verify_admin(access_token: Optional[str] = Cookie(None)):
    """Dependency to verify admin role"""
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    role = keycloak_service.get_athenas_role(access_token)
    if role != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return access_token

# Department management
@router.get("/departments", response_model=List[Department])
async def list_departments(
    active_only: bool = False,
    _: str = Depends(verify_admin)
):
    """List all departments"""
    departments = await storage_service.get_departments(active_only=active_only)
    return departments

@router.post("/departments", response_model=dict)
async def create_department(
    dept: DepartmentCreate,
    _: str = Depends(verify_admin)
):
    """Create new department"""
    dept_id = await storage_service.add_department(dept.name, dept.active)
    return {"id": dept_id, "message": "Department created successfully"}

@router.put("/departments/{dept_id}")
async def update_department(
    dept_id: int,
    dept: DepartmentCreate,
    _: str = Depends(verify_admin)
):
    """Update department"""
    await storage_service.update_department(dept_id, dept.name, dept.active)
    return {"message": "Department updated successfully"}

@router.delete("/departments/{dept_id}")
async def delete_department(
    dept_id: int,
    _: str = Depends(verify_admin)
):
    """Delete department"""
    await storage_service.delete_department(dept_id)
    return {"message": "Department deleted successfully"}

# Rubric management
@router.get("/rubrics")
async def list_rubrics(_: str = Depends(verify_admin)):
    """List all rubric files"""
    # This will scan the rubricas directory
    import os
    rubrics_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "rubricas")
    
    if not os.path.exists(rubrics_dir):
        return []
    
    rubrics = []
    for filename in os.listdir(rubrics_dir):
        if filename.endswith('.json'):
            rubrics.append({
                "filename": filename,
                "department": filename.replace('.json', '')
            })
    
    return rubrics

@router.post("/rubrics/upload")
async def upload_rubric(
    department: str,
    rubric_data: dict,
    _: str = Depends(verify_admin)
):
    """Upload new rubric JSON"""
    import json
    rubrics_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "rubricas")
    os.makedirs(rubrics_dir, exist_ok=True)
    
    filepath = os.path.join(rubrics_dir, f"{department}.json")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(rubric_data, f, ensure_ascii=False, indent=2)
    
    return {"message": "Rubric uploaded successfully", "filepath": filepath}

@router.delete("/rubrics/{department}")
async def delete_rubric(
    department: str,
    _: str = Depends(verify_admin)
):
    """Delete rubric file"""
    import os
    rubrics_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "rubricas")
    filepath = os.path.join(rubrics_dir, f"{department}.json")
    
    if os.path.exists(filepath):
        os.remove(filepath)
        return {"message": "Rubric deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Rubric not found")

# User management
@router.get("/users")
async def list_users(_: str = Depends(verify_admin)):
    """List all users"""
    # This would query the database for users
    # For now, return placeholder
    return {"message": "User management coming soon"}
