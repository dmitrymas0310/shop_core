from uuid import UUID
from typing import Optional, Any
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.db import get_session
from app.users.models import User, UserRole


class UserRepository:
  def __init__(self, db: AsyncSession):
    self.db = db
  
  async def create_user(self, first_name: str, last_name: str, login: str, password_hash: str, role: UserRole) -> User:
    user = User(
      first_name = first_name,
      last_name = last_name,
      login = login,
      password_hash = password_hash,
      role = role
    )
    self.db.add(user)
    await self.db.commit()
    await self.db.refresh(user)
    return user 
  
  async def get_by_login(self, login: str) -> Optional[User]:
    result = await self.db.execute(select(User).where(User.login == login))
    return result.scalar_one_or_none()
  
  async def get_by_id(self, id: UUID) -> Optional[User]:
    result = await self.db.execute(select(User).where(User.id == id))
    return result.scalar_one_or_none()

  async def get_all(self, limit: int = 100, skip: int = 0) -> list[User]:
    result = await self.db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()
  
  async def update_user(self, user_id: UUID, data: dict[str, Any]) -> User:
    user = update(User).where(User.id == user_id).values(**data).returning(User)
    result = await self.db.execute(user)
    await self.db.commit()
    return result.scalar_one()
  
  async def update_password(self, user_id: UUID, new_hash: str) -> None:
    user = update(User).where(User.id == user_id).values(password_hash=new_hash)
    await self.db.execute(user)
    await self.db.commit()

  async def exists_by_login(self, login: str) -> bool:
    user = select(User.id).where(User.login == login)
    result = await self.db.execute(user)
    return result.scalar_one_or_none() is not None


async def get_user_repository(db: AsyncSession = Depends(get_session)) -> UserRepository:
  return UserRepository(db)