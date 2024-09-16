from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from api.utils import password_utils
from api.core import response_messages
from api.v1.schemas import auth as auth_schema
from api.v1.models.user import User


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
