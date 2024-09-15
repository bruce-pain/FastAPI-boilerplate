from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional

from api.core.config import settings


class TokenData(BaseModel):
    """schema to structure token data"""

    id = Optional[str]


def create_access_token(user_id: str) -> str:
    """Function to create an access token"""

    expire = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRY)
    data = {"user_id": user_id, "exp": expire, "type": "access"}
    encoded_jwt = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_access_token(access_token: str, credentials_exception):
    """Funtcion to decode and verify access token"""

    try:
        payload = jwt.decode(
            access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("user_id")
        token_type = payload.get("type")

        if user_id is None:
            raise credentials_exception

        if token_type == "refresh":
            raise HTTPException(detail="Refresh token not allowed", status_code=400)

        token_data = TokenData(id=user_id)

    except JWTError:
        raise credentials_exception

    return token_data
