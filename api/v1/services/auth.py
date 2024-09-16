from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from starlette.config import Config
from authlib.integrations.starlette_client import OAuth

from api.utils import password_utils
from api.core import response_messages
from api.core.config import settings
from api.v1.schemas import auth as auth_schema
from api.v1.models.user import User


config_data = {
    "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": settings.GOOGLE_CLIENT_SECRET,
}

starlette_config = Config(environ=config_data)

oauth = OAuth(starlette_config)

oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def register(db: Session, schema: auth_schema.RegisterRequest) -> User:
    """Creates a new user

    Args:
        db (Session): Database Session
        schema (auth_schema.RegisterRequest): Registration schema

    Returns:
        User: User object for the newly created user
    """

    # check if user with email already exists
    if db.query(User).filter(User.email == schema.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response_messages.EMAIL_ALREADY_EXISTS,
        )

    # Hash password
    schema.password = password_utils.hash_password(password=schema.password)

    user = User(**schema.model_dump())

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def google_register(db: Session, schema: auth_schema.RegisterRequest) -> User:
    """Create a new user from google login

    Args:
        db (Session): Database Session
        schema (auth_schema.RegisterRequest): Registration schema

    Returns:
        User: User object for newly created user
    """

    # check if user with email already exists
    existing_user = db.query(User).filter(User.email == schema.email).first()

    if existing_user:
        return existing_user

    user = User(**schema.model_dump())

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate(db: Session, schema: auth_schema.LoginRequest) -> User:
    """Authenticates a registered user

    Args:
        db (Session): Database Session
        schema (auth_schema.LoginRequest): Login Request schema

    Returns:
        User: Authenticated user
    """

    # check if user with the email exists
    user = db.query(User).filter(User.email == schema.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response_messages.INVALID_EMAIL,
        )

    if not password_utils.verify_password(schema.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response_messages.INVALID_PASSWORD,
        )

    return user
