from datetime import UTC, datetime, timedelta
from typing import Optional

from fastapi import HTTPException
from jose import JWTError, jwt

from app.core import response_messages
from app.core.config import settings


def create_jwt_token(token_type: str, user_id: str) -> str:
    expiry_period = {
        "access": settings.ACCESS_TOKEN_EXPIRY,
        "refresh": settings.REFRESH_TOKEN_EXPIRY,
    }

    if token_type not in expiry_period.keys():
        raise ValueError("token_type should be 'access' or 'refresh'")

    expire = datetime.now(UTC) + timedelta(hours=expiry_period[token_type])
    data = {"user_id": user_id, "exp": expire, "type": token_type}
    encoded_jwt = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_jwt_token(token: str, credentials_exception: HTTPException) -> str:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str | None = payload.get("user_id")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    return user_id


def refresh_access_token(refresh_token: str) -> Optional[str]:
    credentials_exception = HTTPException(
        status_code=401, detail=response_messages.EXPIRED_REFRESH_TOKEN
    )

    user_id = verify_jwt_token(
        token=refresh_token, credentials_exception=credentials_exception
    )

    if user_id:
        new_access_token = create_jwt_token("access", user_id=user_id)
        return new_access_token
