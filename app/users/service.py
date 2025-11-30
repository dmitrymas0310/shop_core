from uuid import UUID

from fastapi import Depends, HTTPException, status

from app.users.repository import UserRepository, get_user_repository
from app.users.schemas import UserCreate, UserUpdate, UserRead, UserChangePassword
from app.core.security import hash_password, verify_password


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo
    
    async def register_user(self, data: UserCreate) -> UserRead:
        if await self.repo.exists_by_login(data.login):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this login already exists",
            )

        password_hash = hash_password(data.password)

        user = await self.repo.create_user(
            first_name=data.first_name,
            last_name=data.last_name,
            login=data.login,
            password_hash=password_hash,
            role=data.role,
        )

        #Валидация работает при добавлении class Config: from_attributes = True в schemas.UserRead
        return UserRead.model_validate(user)
    
    async def get_user(self, user_id: UUID) -> UserRead:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return UserRead.model_validate(user)

    async def list_users(self, limit: int = 100, skip: int = 0) -> list[UserRead]:
        users = await self.repo.get_all(limit=limit, skip=skip)
        return [UserRead.model_validate(u) for u in users]

    async def update_user(self, user_id: UUID, data: UserUpdate) -> UserRead:
        update_data = data.model_dump(exclude_unset=True)

        if not update_data:
            user = await self.repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found",
                )
            return UserRead.model_validate(user)

        user = await self.repo.update_user(user_id, update_data)
        return UserRead.model_validate(user)

    async def change_password(self, user_id: UUID, payload: UserChangePassword) -> None:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if not verify_password(payload.old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password",
            )

        new_hash = hash_password(payload.new_password)
        await self.repo.update_password(user_id, new_hash)





async def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)
