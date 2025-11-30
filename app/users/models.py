from typing import Any
from sqlalchemy import Column, String, Enum as SAEnum

from app.core.db import Base, BaseModelMixin
from app.users.enum import UserRole



class User(Base, BaseModelMixin):
    __tablename__= "users"

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    login = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    role = Column(SAEnum(UserRole, name="user_role_enum"), nullable=False, default=UserRole.USER)

    def __repr__(self) -> str:
        return f"id - {self.id}, first_name - {self.first_name}, last_name- {self.last_name}, , login- {self.login}, role- {self.role}"
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "login": self.login,
            "role": self.role
        }










