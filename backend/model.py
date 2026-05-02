from pydantic import BaseModel
from pydantic import ConfigDict
from datetime import datetime
from typing import Optional


class UserLogin(BaseModel):
    """User login schema"""
    email: str
    password: str


class UserRegister(UserLogin):
    """User registration schema"""
    full_name: Optional[str] = None
    name: Optional[str] = None


class loginresponse(BaseModel):
    """Login response schema"""
    id: int
    email: str
    full_name: str
    is_active: int
    role: str
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Fields allowed when updating a user"""
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[int] = None


class UserResponse(BaseModel):
    """User response schema"""
    id: int
    email: str
    full_name: str
    password: Optional[str] = None
    is_active: int
    role: str
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
