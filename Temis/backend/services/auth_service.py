#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Authentication service for TEMIS
Integrates with Keycloak
"""

import requests
from jose import jwt, JWTError
from datetime import datetime
from typing import Optional, Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.keycloak_config import (
    KEYCLOAK_URL,
    REALM,
    CLIENT_ID,
    CLIENT_SECRET,
    USERINFO_ENDPOINT,
    PRIMARY_OWNER_EMAIL
)


class AuthService:
    """Authentication service"""

    @staticmethod
    def validate_token(access_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate access token with Keycloak
        Returns user info if valid, None otherwise
        """
        try:
            # Get user info from Keycloak
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(USERINFO_ENDPOINT, headers=headers)
            
            if response.status_code == 200:
                user_info = response.json()
                return {
                    "keycloak_id": user_info.get("sub"),
                    "email": user_info.get("email"),
                    "name": user_info.get("name", user_info.get("preferred_username")),
                    "email_verified": user_info.get("email_verified", False)
                }
            return None
        except Exception as e:
            print(f"Error validating token: {e}")
            return None

    @staticmethod
    def determine_user_role(email: str) -> str:
        """
        Determine user role based on email
        """
        if email == PRIMARY_OWNER_EMAIL:
            return "primary_owner"
        return "member"  # Default role

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Decode JWT token (without validation for now)
        """
        try:
            # Decode without verification (Keycloak already validated)
            payload = jwt.get_unverified_claims(token)
            return payload
        except JWTError:
            return None
