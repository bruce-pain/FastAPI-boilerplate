from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from authlib.integrations.base_client import OAuthError
from authlib.oauth2.rfc6749 import OAuth2Token

from app.core import response_messages
from app.db.database import get_db
from app.utils import jwt_helpers
from app.core.dependencies.security import get_current_user
from app.core.config import settings

from app.api.v1.auth import schemas, services
from app.api.models.user import User

auth = APIRouter(prefix="/auth", tags=["Authentication"])


@auth.post(
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
    """Endpoint for a user to register their account

    Args:
    schema (schemas.LoginRequest): Login request schema
    db (Annotated[Session, Depends): Database session
    """

    # Create user account

    user = services.register(db=db, schema=schema)

    # Create access and refresh tokens
    access_token = jwt_helpers.create_jwt_token("access", user.id)
    refresh_token = jwt_helpers.create_jwt_token("refresh", user.id)

    response_data = schemas.AuthResponseData(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    return schemas.AuthResponse(
        status_code=status.HTTP_201_CREATED,
        message=response_messages.REGISTER_SUCCESSFUL,
        access_token=access_token,
        refresh_token=refresh_token,
        data=response_data,
    )


@auth.post(
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
    """Endpoint for user login

    Args:
        schema (schemas.LoginRequest): Login request schema
        db (Annotated[Session, Depends): Database session
    """

    user = services.authenticate(db=db, schema=schema)

    # Create access and refresh tokens
    access_token = jwt_helpers.create_jwt_token("access", user.id)
    refresh_token = jwt_helpers.create_jwt_token("refresh", user.id)

    response_data = schemas.AuthResponseData(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    return schemas.AuthResponse(
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
    return await services.oauth.google.authorize_redirect(
        request, settings.GOOGLE_REDIRECT_URL
    )


@auth.get(
    path="/callback/google",
    response_model=schemas.AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gooogle auth redirect",
    description="After the google login, the user will be redirected to this endpoint, which returns user data and tokens",
    tags=["Authentication"],
)
async def google_callback(request: Request, db: Annotated[Session, Depends(get_db)]):
    try:
        user_response: OAuth2Token = await services.oauth.google.authorize_access_token(
            request
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

    schema = schemas.RegisterRequest(**user_info)
    user = services.google_register(db=db, schema=schema)

    # Create access and refresh tokens
    access_token = jwt_helpers.create_jwt_token("access", user.id)
    refresh_token = jwt_helpers.create_jwt_token("refresh", user.id)

    response_data = schemas.AuthResponseData(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    return schemas.AuthResponse(
        status_code=status.HTTP_201_CREATED,
        message=response_messages.REGISTER_SUCCESSFUL,
        access_token=access_token,
        refresh_token=refresh_token,
        data=response_data,
    )


@auth.post(
    path="/token/refresh",
    response_model=schemas.TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh tokens",
    description="This endpoint uses the current refresh token to create new access and refresh tokens",
    tags=["Authentication"],
)
def refresh_token(schema: schemas.TokenRefreshRequest):
    """Endpoint to refresh the access token

    Args:
        schema (schemas.TokenRefreshRequest): Refresh Token Schema

    Returns:
        _type_: Refresh Token Response
    """
    token = jwt_helpers.refresh_access_token(refresh_token=schema.refresh_token)

    return schemas.TokenRefreshResponse(
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
