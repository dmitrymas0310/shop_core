from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.auth.schemas import Token, Login, RefreshRequest
from app.auth.service import AuthService, get_auth_service, get_req_service
from app.users.service import UserService, get_user_service
from app.users.schemas import UserCreate, UserRead  

router = APIRouter()


@router.post("/registrate", response_model=UserRead, summary="Создаёт нового пользователя в системе",)
async def registrate(
    form_data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    user = await service.register_user(form_data)
    return user


@router.post("/token", response_model=Token, summary="Аутентификация пользователя и выдача access-токена",)
async def login_for_access_token(
    form_data: Login,
    service: AuthService = Depends(get_req_service),
):
    user = await service.authenticate_user(form_data.login, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=settings.auth.access_token_expire_minutes
    )

    access_token = service.create_access_token(
        data={"sub": user.login},
        expires_minutes=settings.auth.access_token_expire_minutes,
    )
    refresh_token = service.create_refresh_token(
        data={"sub": user.login}
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token, summary="Обновляет access и refresh токены пользователя",)
async def refresh_tokens(
    body: RefreshRequest,
    service: AuthService = Depends(get_req_service),
):
    access_token, refresh_token = await service.refresh_tokens(body)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.get("/users/me", response_model=UserRead, summary="Возвращает данные авторизованного пользователя",)
async def read_users_me(
    service: AuthService = Depends(get_auth_service),
):
    current_user = await service.get_current_user()
    return current_user


@router.get("/protected", summary="Cлужебный защищённый эндпоинт",)
async def protected_route(
    service: AuthService = Depends(get_auth_service),
):
    current_user = await service.get_current_user()

    return {
        "message": (
            f"Hello {current_user.first_name if current_user.first_name else current_user.login}, "
            f"this is a protected route!"
        )
    }