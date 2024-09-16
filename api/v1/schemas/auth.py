from typing import Annotated, Optional

from pydantic import BaseModel, EmailStr, StringConstraints
from api.v1.schemas.base_schema import BaseResponseModel


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: Annotated[str, StringConstraints(max_length=70)]
    last_name: Annotated[str, StringConstraints(max_length=70)]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponseData(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str


class AuthResponse(BaseResponseModel):
    access_token: str
    refresh_token: str
    data: AuthResponseData