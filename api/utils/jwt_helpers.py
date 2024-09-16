from datetime import datetime, timedelta

from api.core.config import settings
from fastapi import HTTPException
from jose import JWTError, jwt
from api.v1.schemas.auth import TokenData


def create_jwt_token(token_type: str, user_id: str) -> str:
    """Function to create an access token"""

    expiry_period = {
        "access": settings.ACCESS_TOKEN_EXPIRY,
        "refresh": settings.REFRESH_TOKEN_EXPIRY,
    }

    if token_type not in expiry_period.keys():
        raise ValueError("token_type should be 'access' or 'refresh'")

    expire = datetime.utcnow() + timedelta(hours=expiry_period[token_type])
    data = {"user_id": user_id, "exp": expire, "type": token_type}
    encoded_jwt = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_jwt_token(token: str, credentials_exception: HTTPException) -> str:
    """Funtcion to decode and verify access and refresh tokens"""

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("user_id")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    return user_id
