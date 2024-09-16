from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from api.core import response_messages
from api.db.database import get_db
from api.utils import jwt_helpers
from api.v1.schemas import auth as auth_schema
from api.v1.services import auth as auth_service

auth = APIRouter(prefix="/auth", tags=["Authentication"])


@auth.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=auth_schema.AuthResponse,
)
def register(
    request: Request,
    response: Response,
    schema: auth_schema.RegisterRequest,
    db: Session = Depends(get_db),
):
    """Endpoint for a user to register their account"""

    # Create user account

    user = auth_service.register(db=db, schema=schema)

    # Create access and refresh tokens
    access_token = jwt_helpers.create_jwt_token("access", user.id)
    refresh_token = jwt_helpers.create_jwt_token("refresh", user.id)

    response_data = auth_schema.AuthResponseData(
        id=user.id, email="", first_name="", last_name=""
    )

    return auth_schema.AuthResponse(
        status_code=status.HTTP_201_CREATED,
        message=response_messages.REGISTER_SUCCESSFUL,
        access_token=access_token,
        refresh_token=refresh_token,
        data=response_data,
    )
