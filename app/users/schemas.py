from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from app.users.enum import UserRole


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    login: str 
    password: str
    role: UserRole = UserRole.USER

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserChangePassword(BaseModel):
    old_password: str
    new_password: str 

class UserRead(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    login: str
    role: UserRole
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
