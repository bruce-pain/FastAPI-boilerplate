from fastapi import APIRouter, Depends, Request, Query, BackgroundTasks
from sqlalchemy.orm import Session
from api.v1.schemas.request_password_reset import RequestEmail, ResetPassword, ResetPasswordResponse
from api.db.database import get_db as get_session
from api.v1.services.request_pwd import reset_service
from api.utils.success_response import success_response
from api.v1.services.user import user_service
from api.v1.models.user import User

pwd_reset = APIRouter(prefix="/auth", tags=["Authentication"])


# generate password reset link
@pwd_reset.post("/request-forget-password")

async def request_forget_password(
    reset_schema: RequestEmail,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_session),
):
    url = "api/v1/auth/forget-password"
    template_file = "reset_password.html"
    subject = "HNG11 PASSWORD RESET"
    data = await reset_service.create(reset_schema, request, db, background_tasks,
                                      subject=subject, template_file=template_file, url=url)
    return success_response(**data)

# process password link


@pwd_reset.get("/forget-password")
async def process_forget_password_link(
    token: str = Query(...), db: Session = Depends(get_session)
):
    return reset_service.process_reset_link(token, db)


# change the password
@pwd_reset.post("/forget-password")
async def forget_password(
    data: ResetPassword,
    token: str = Query(...),
    session: Session = Depends(get_session),
):
    return reset_service.reset_password(data, token, session)

# change the password


@pwd_reset.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    data: ResetPassword,
    session: Session = Depends(get_session),
    current_user: User = Depends(user_service.get_current_user)
):
    return reset_service.reset_user_password(data, session, current_user)
