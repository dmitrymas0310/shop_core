from typing import Optional
from pydantic import BaseModel



class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    login: Optional[str] = None

class Login(BaseModel):
    login: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str
