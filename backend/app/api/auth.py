"""
Authentication and User Profile Endpoints.
Implements Module 1 (User & Authentication).
"""

from typing import Dict
from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas.enums import UserRole

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    name: str
    role: UserRole
    organization_id: str


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user():
    """
    Returns active user profile and roles for session management.
    """
    return UserProfileResponse(
        user_id="usr-default-admin",
        email="admin@decisioncourt.ai",
        name="Chief Decision Officer",
        role=UserRole.ADMIN,
        organization_id="default_org",
    )
