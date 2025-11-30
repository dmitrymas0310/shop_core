from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, status

from app.users.service import UserService, get_user_service
from app.users.schemas import UserCreate, UserRead, UserUpdate, UserChangePassword

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Зарегистрировать нового пользователя",
)
async def register_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.register_user(payload)

@router.get(
    "/",
    response_model=List[UserRead],
    summary="Получить список пользователей",
)
async def list_users(
    limit: int = 100,
    skip: int = 0,
    service: UserService = Depends(get_user_service),
) -> List[UserRead]:
    return await service.list_users(limit=limit, skip=skip)

@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Получить пользователя по ID",
)
async def get_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.get_user(user_id)

@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Обновить данные пользователя",
)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    return await service.update_user(user_id, payload)

@router.post(
    "/{user_id}/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Сменить пароль пользователя",
)
async def change_password(
    user_id: UUID,
    payload: UserChangePassword,
    service: UserService = Depends(get_user_service),
) -> None:

    await service.change_password(user_id, payload)
