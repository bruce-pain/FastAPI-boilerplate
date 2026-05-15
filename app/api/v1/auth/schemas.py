from typing import Annotated

from pydantic import BaseModel, EmailStr, StringConstraints

from app.core.base.schema import BaseResponseModel


class RegisterRequest(BaseModel):
    password: str
    email: Annotated[EmailStr, StringConstraints(max_length=254)]


class LoginRequest(BaseModel):
    email: Annotated[EmailStr, StringConstraints(max_length=254)]
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseResponseModel):
    access_token: str


class AuthResponseData(BaseModel):
    id: str
    email: EmailStr


class AuthResponse(BaseResponseModel):
    access_token: str
    refresh_token: str
    data: AuthResponseData


class UserResponse(BaseResponseModel):
    data: AuthResponseData

