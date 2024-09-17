from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from authlib.integrations.base_client import OAuthError
from authlib.oauth2.rfc6749 import OAuth2Token

from api.core import response_messages
from api.db.database import get_db
from api.utils import jwt_helpers
from api.core.dependencies.security import get_current_user
from api.core.config import settings
from api.v1.schemas import auth as auth_schema
from api.v1.services import auth as auth_service
from api.v1.models import User

auth = APIRouter(prefix="/auth", tags=["Authentication"])


@auth.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=auth_schema.AuthResponse,
    summary="Create a new user account",
    description="This endpoint takes in the user creation details and returns jwt tokens along with user data",
    tags=["Authentication"],
)
def register(
    schema: auth_schema.RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Endpoint for a user to register their account

    Args:
    schema (auth_schema.LoginRequest): Login request schema
    db (Annotated[Session, Depends): Database session
    """

    # Create user account

    user = auth_service.register(db=db, schema=schema)

    # Create access and refresh tokens
    access_token = jwt_helpers.create_jwt_token("access", user.id)
    refresh_token = jwt_helpers.create_jwt_token("refresh", user.id)

    response_data = auth_schema.AuthResponseData(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    return auth_schema.AuthResponse(
        status_code=status.HTTP_201_CREATED,
        message=response_messages.REGISTER_SUCCESSFUL,
        access_token=access_token,
        refresh_token=refresh_token,
        data=response_data,
    )


@auth.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    response_model=auth_schema.AuthResponse,
    summary="Login a registered user",
    description="This endpoint retrieves the jwt tokens for a registered user",
    tags=["Authentication"],
)
def login(
    schema: auth_schema.LoginRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Endpoint for user login

    Args:
        schema (auth_schema.LoginRequest): Login request schema
        db (Annotated[Session, Depends): Database session
    """

    user = auth_service.authenticate(db=db, schema=schema)

    # Create access and refresh tokens
    access_token = jwt_helpers.create_jwt_token("access", user.id)
    refresh_token = jwt_helpers.create_jwt_token("refresh", user.id)

    response_data = auth_schema.AuthResponseData(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    return auth_schema.AuthResponse(
        status_code=status.HTTP_201_CREATED,
        message=response_messages.REGISTER_SUCCESSFUL,
        access_token=access_token,
        refresh_token=refresh_token,
        data=response_data,
    )


@auth.get(
    path="/google",
    summary="Initiate Google auth flow",
    description="This endpoint starts the google oauth process",
    tags=["Authentication"],
)
async def google_init(request: Request):
    return await auth_service.oauth.google.authorize_redirect(
        request, settings.GOOGLE_REDIRECT_URL
    )


@auth.get(
    path="/callback/google",
    response_model=auth_schema.AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gooogle auth redirect",
    description="After the google login, the user will be redirected to this endpoint, which returns user data and tokens",
    tags=["Authentication"],
)
async def google_callback(request: Request, db: Annotated[Session, Depends(get_db)]):
    try:
        user_response: OAuth2Token = (
            await auth_service.oauth.google.authorize_access_token(request)
        )
    except OAuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=response_messages.INVALID_CREDENTIALS,
        )

    user_info = user_response.get("userinfo")
    user_info = {
        "first_name": user_info["given_name"],
        "last_name": user_info["family_name"],
        "email": user_info["email"],
    }

    schema = auth_schema.RegisterRequest(**user_info)
    user = auth_service.google_register(db=db, schema=schema)

    # Create access and refresh tokens
    access_token = jwt_helpers.create_jwt_token("access", user.id)
    refresh_token = jwt_helpers.create_jwt_token("refresh", user.id)

    response_data = auth_schema.AuthResponseData(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    return auth_schema.AuthResponse(
        status_code=status.HTTP_201_CREATED,
        message=response_messages.REGISTER_SUCCESSFUL,
        access_token=access_token,
        refresh_token=refresh_token,
        data=response_data,
    )


@auth.post(
    path="/token/refresh",
    response_model=auth_schema.TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh tokens",
    description="This endpoint uses the current refresh token to create new access and refresh tokens",
    tags=["Authentication"],
)
def refresh_token(schema: auth_schema.TokenRefreshRequest):
    """Endpoint to refresh the access token

    Args:
        schema (auth_schema.TokenRefreshRequest): Refresh Token Schema

    Returns:
        _type_: Refresh Token Response
    """
    token = jwt_helpers.refresh_access_token(refresh_token=schema.refresh_token)

    return auth_schema.TokenRefreshResponse(
        status_code=status.HTTP_200_OK,
        message=response_messages.TOKEN_REFRESH_SUCCESSFUL,
        access_token=token,
    )


@auth.get("/greet/user")
def greet(current_user: Annotated[User, Depends(get_current_user)]):
    """Protected route to greet the current user

    Args:
        current_user (Annotated[User, Depends): The currently logged in user
    """

    return {"greeting": f"Hello, {current_user.first_name}!"}
