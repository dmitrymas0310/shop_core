from datetime import timedelta, datetime

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt


from app.users.repository import UserRepository, get_user_repository
from app.users.models import User 
from app.users.enum import UserRole
from app.core.config import settings
from app.core.security import verify_password
from app.auth.schemas import TokenData, RefreshRequest


security = HTTPBearer()

class AuthService:
    def __init__(
            self,
            repo: UserRepository,
            credentials: Optional[HTTPAuthorizationCredentials] = None
    ):
        self.repo = repo
        self.credentials = credentials

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)
    
    async def authenticate_user(self, login: str, password: str) -> Optional[User]:
        user = await self.repo.get_by_login(login)

        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
    
    def _create_token(self, data: dict, expired_delta: timedelta) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + expired_delta
        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(
            to_encode,
            settings.auth.secret_key,
            algorithm=settings.auth.algorithm
        ) 

        return encoded_jwt
    
    def create_access_token(self, data: dict, expires_minutes: int | None = None) -> str:
        minutes = (
            expires_minutes
            if expires_minutes is not None
            else settings.auth.access_token_expire_minutes
        )
        return self._create_token(data, timedelta(minutes=minutes))
    
    def create_refresh_token(self, data: dict) -> str:
        expires = timedelta(days=settings.auth.refresh_token_expire_days)
        payload = data.copy()
        payload["type"] = "refresh"
        return self._create_token(payload, expires)
    
    async def get_current_user(self):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if self.credentials is None:
            raise credentials_exception

        token = self.credentials.credentials

        try:
            payload = jwt.decode(
                token,
                settings.auth.secret_key,
                algorithms=[settings.auth.algorithm],
            )
            login: str | None = payload.get("sub")
            if login is None:
                raise credentials_exception
            _ = TokenData(login=login)
        except JWTError:
            raise credentials_exception

        user = await self.repo.get_by_login(login)

        if user is None:
            raise credentials_exception

        return user
    
    async def refresh_tokens(self, data: RefreshRequest) -> tuple[str, str]:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(
                data.refresh_token,
                settings.auth.secret_key,
                algorithms=[settings.auth.algorithm],
            )
            if payload.get("type") != "refresh":
                raise credentials_exception

            login: str | None = payload.get("sub")
            if login is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = await self.repo.get_by_login(login)
        if user is None:
            raise credentials_exception

        access_token = self.create_access_token({"sub": user.login})
        refresh_token = self.create_refresh_token({"sub": user.login})

        return access_token, refresh_token

async def get_req_service(
    repo: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(repo)


async def get_auth_service(
    repo: UserRepository = Depends(get_user_repository),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthService:
    return AuthService(repo, credentials)

async def get_current_user_dep(
    auth: AuthService = Depends(get_auth_service),
) -> User:
    return await auth.get_current_user()

async def require_admin(
    current_user: User = Depends(get_current_user_dep),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user