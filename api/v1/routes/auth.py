from fastapi import (
    APIRouter,
    Depends,
    status,
)
from sqlalchemy.orm import Session
from typing import Annotated

from api.core import response_messages
from api.db.database import get_db
from api.utils import jwt_helpers
from api.core.dependencies.security import get_current_user
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


@auth.get("/greet/user")
def greet(current_user: Annotated[User, Depends(get_current_user)]):
    """Protected route to greet the current user

    Args:
        current_user (Annotated[User, Depends): The currently logged in user
    """

    return {"greeting": f"Hello, {current_user.first_name}!"}
