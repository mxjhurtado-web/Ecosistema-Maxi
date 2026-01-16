#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Groups router for TEMIS
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from backend.database import get_db
from backend.models.user import User
from backend.models.group import Group, GroupMember, GroupMemberRole

router = APIRouter()


class GroupCreate(BaseModel):
    """Group creation request"""
    name: str
    description: Optional[str] = None


class GroupResponse(BaseModel):
    """Group response"""
    id: str
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=GroupResponse)
def create_group(
    group_data: GroupCreate,
    user_email: str,
    db: Session = Depends(get_db)
):
    """Create new group"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    group = Group(
        name=group_data.name,
        description=group_data.description,
        created_by=user.id
    )
    db.add(group)
    db.flush()

    # Add creator as admin
    group_member = GroupMember(
        group_id=group.id,
        user_id=user.id,
        role=GroupMemberRole.ADMIN
    )
    db.add(group_member)

    db.commit()
    db.refresh(group)

    return group


@router.get("/", response_model=List[GroupResponse])
def list_groups(
    user_email: str,
    db: Session = Depends(get_db)
):
    """List user's groups"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    groups = db.query(Group).join(GroupMember).filter(
        GroupMember.user_id == user.id
    ).all()

    return groups
