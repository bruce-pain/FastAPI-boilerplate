from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.features.auth import schemas as auth_schemas
from app.features.auth.models import User
from app.features.auth.password import hash_password, verify_password
from app.features.auth.repository import UserRepository


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def register(self, schema: auth_schemas.RegisterRequest) -> User:
        if self.repository.get_by_email(schema.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists!",
            )

        schema.password = hash_password(password=schema.password)

        user = User(**schema.model_dump())

        logger.info(f"Creating user with email: {user.email}")
        return self.repository.create(user)

    def authenticate(self, schema: auth_schemas.LoginRequest) -> User:
        user = self.repository.get_by_email(schema.email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email",
            )

        if not verify_password(schema.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password",
            )

        logger.info(f"User authenticated with email: {user.email}")
        return user
