from typing import Annotated

from pydantic import BaseModel, StringConstraints, EmailStr
from app.core.base.schema import BaseResponseModel


class RegisterRequest(BaseModel):
    password: str
    email: Annotated[EmailStr, StringConstraints(max_length=254)]
    username: Annotated[str, StringConstraints(max_length=70)]


class LoginRequest(BaseModel):
    email: Annotated[EmailStr, StringConstraints(max_length=254)]
    password: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseResponseModel):
    access_token: str


class AuthResponseData(BaseModel):
    id: str
    username: str
    email: EmailStr


class AuthResponse(BaseResponseModel):
    access_token: str
    refresh_token: str
    data: AuthResponseData

class UserResponse(BaseResponseModel):
    data: AuthResponseData