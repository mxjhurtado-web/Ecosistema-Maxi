#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Project members router for TEMIS
Handles project member management and role assignment
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from backend.database import get_db
from backend.models.user import User
from backend.models.project import Project, ProjectMember, ProjectMemberRole
from backend.models.project_roles import ProjectRole

router = APIRouter()


class MemberResponse(BaseModel):
    """Project member response"""
    user_id: str
    email: str
    name: Optional[str]
    role: str
    project_roles: List[str] = []
    
    class Config:
        from_attributes = True


class AddMemberRequest(BaseModel):
    """Add member to project"""
    email: str
    role: str = "MEMBER"


class AssignRoleRequest(BaseModel):
    """Assign project role to member"""
    user_id: str
    project_role: str


@router.get("/{project_id}/members", response_model=List[MemberResponse])
def get_project_members(
    project_id: str,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Get all members of a project"""
    # Verify user has access
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user is member of project
    is_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id
    ).first()
    
    if not is_member:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get all members
    members = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id
    ).all()
    
    result = []
    for member in members:
        member_user = db.query(User).filter(User.id == member.user_id).first()
        if member_user:
            result.append({
                "user_id": str(member.user_id),
                "email": member_user.email,
                "name": member_user.name,
                "role": member.role.value,
                "project_roles": member.project_roles if member.project_roles else []
            })
    
    return result


@router.post("/{project_id}/members")
def add_project_member(
    project_id: str,
    request: AddMemberRequest,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Add member to project (owner only)"""
    # Verify requester is owner
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    requester_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id,
        ProjectMember.role == ProjectMemberRole.OWNER
    ).first()
    
    if not requester_member:
        raise HTTPException(status_code=403, detail="Only owners can add members")
    
    # Find user to add
    new_user = db.query(User).filter(User.email == request.email).first()
    if not new_user:
        # Create user if doesn't exist
        new_user = User(email=request.email, name=request.email.split('@')[0])
        db.add(new_user)
        db.flush()
    
    # Check if already member
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == new_user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")
    
    # Add member
    member = ProjectMember(
        project_id=project_id,
        user_id=new_user.id,
        role=ProjectMemberRole[request.role.upper()]
    )
    db.add(member)
    db.commit()
    
    return {"message": "Member added successfully"}


@router.post("/{project_id}/members/assign-role")
def assign_project_role(
    project_id: str,
    request: AssignRoleRequest,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Assign framework role to project member (owner only)"""
    # Verify requester is owner
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    requester_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id,
        ProjectMember.role == ProjectMemberRole.OWNER
    ).first()
    
    if not requester_member:
        raise HTTPException(status_code=403, detail="Only owners can assign roles")
    
    # Verify role is valid
    try:
        role = ProjectRole[request.project_role.upper().replace(" ", "_")]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid project role")
    
    # Get member to update
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == request.user_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Add role to project_roles list
    if not member.project_roles:
        member.project_roles = []
    
    if request.project_role not in member.project_roles:
        member.project_roles.append(request.project_role)
    
    db.commit()
    
    return {"message": "Role assigned successfully"}


@router.delete("/{project_id}/members/{user_id}")
def remove_project_member(
    project_id: str,
    user_id: str,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Remove member from project (owner only)"""
    # Verify requester is owner
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    requester_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user.id,
        ProjectMember.role == ProjectMemberRole.OWNER
    ).first()
    
    if not requester_member:
        raise HTTPException(status_code=403, detail="Only owners can remove members")
    
    # Can't remove yourself if you're the only owner
    if str(user.id) == user_id:
        owners_count = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.role == ProjectMemberRole.OWNER
        ).count()
        
        if owners_count == 1:
            raise HTTPException(status_code=400, detail="Cannot remove the only owner")
    
    # Remove member
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    db.delete(member)
    db.commit()
    
    return {"message": "Member removed successfully"}
