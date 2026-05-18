from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies.security import get_current_user
from app.features.auth import schemas
from app.features.auth.jwt import create_jwt_token, refresh_access_token
from app.features.auth.models import User
from app.features.auth.service import UserService

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.AuthResponse,
    summary="Create a new user account",
    description="This endpoint takes in the user creation details and returns jwt tokens along with user data",
    tags=["Authentication"],
)
def register(
    schema: schemas.RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
):
    service = UserService(db=db)

    user = service.register(schema=schema)

    access_token = create_jwt_token("access", user.id)
    refresh_token = create_jwt_token("refresh", user.id)

    response_data = schemas.AuthResponseData(id=user.id, email=user.email)

    return schemas.AuthResponse(
        status_code=status.HTTP_201_CREATED,
        message="User registered successfully",
        access_token=access_token,
        refresh_token=refresh_token,
        data=response_data,
    )


@auth_router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    response_model=schemas.AuthResponse,
    summary="Login a registered user",
    description="This endpoint retrieves the jwt tokens for a registered user",
    tags=["Authentication"],
)
def login(
    schema: schemas.LoginRequest,
    db: Annotated[Session, Depends(get_db)],
):
    service = UserService(db=db)

    user = service.authenticate(schema=schema)

    access_token = create_jwt_token("access", user.id)
    refresh_token = create_jwt_token("refresh", user.id)

    response_data = schemas.AuthResponseData(id=user.id, email=user.email)

    return schemas.AuthResponse(
        status_code=status.HTTP_201_CREATED,
        message="User logged in successfully",
        access_token=access_token,
        refresh_token=refresh_token,
        data=response_data,
    )


@auth_router.post(
    path="/token/refresh",
    response_model=schemas.TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh tokens",
    description="This endpoint uses the current refresh token to create new access and refresh tokens",
    tags=["Authentication"],
)
def refresh_token(schema: schemas.TokenRefreshRequest):
    token = refresh_access_token(refresh_token=schema.refresh_token)

    return schemas.TokenRefreshResponse(
        status_code=status.HTTP_200_OK,
        message="Access token refreshed successfully",
        access_token=token,
    )


@auth_router.get(
    path="/user",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user details",
    description="This endpoint retrieves the details of the logged-in user",
    tags=["Authentication"],
)
def get_user(current_user: Annotated[User, Depends(get_current_user)]):
    user_schema = schemas.AuthResponseData(id=current_user.id, email=current_user.email)

    return schemas.UserResponse(
        status_code=status.HTTP_200_OK,
        message="User Details Retrieved",
        data=user_schema,
    )