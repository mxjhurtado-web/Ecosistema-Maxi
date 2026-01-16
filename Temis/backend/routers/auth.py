#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Authentication router for TEMIS
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db
from backend.services.auth_service import AuthService
from backend.models.user import User, UserRole

router = APIRouter()


class TokenValidation(BaseModel):
    """Token validation request"""
    access_token: str


class UserResponse(BaseModel):
    """User response"""
    id: str
    email: str
    name: str
    role: str

    class Config:
        from_attributes = True


@router.post("/validate")
def validate_token(token_data: TokenValidation, db: Session = Depends(get_db)):
    """
    Validate access token and return user info
    Creates user if doesn't exist
    """
    # Validate token with Keycloak
    user_info = AuthService.validate_token(token_data.access_token)

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    # Check if user exists
    user = db.query(User).filter(User.keycloak_id == user_info["keycloak_id"]).first()

    if not user:
        # Create new user
        role = AuthService.determine_user_role(user_info["email"])
        user = User(
            keycloak_id=user_info["keycloak_id"],
            email=user_info["email"],
            name=user_info["name"],
            role=UserRole(role)
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return {
        "valid": True,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role.value
        }
    }


@router.get("/me")
def get_current_user(token: str, db: Session = Depends(get_db)):
    """Get current user info"""
    user_info = AuthService.validate_token(token)

    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user = db.query(User).filter(User.keycloak_id == user_info["keycloak_id"]).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.from_orm(user)
