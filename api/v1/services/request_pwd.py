from sqlalchemy.orm import Session
from fastapi import HTTPException, Request, Query, Depends, status
from sqlalchemy.exc import SQLAlchemyError
from api.db.database import get_db
from api.utils.success_response import success_response
from api.v1.models.user import User
from api.v1.schemas import request_password_reset
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import BackgroundTasks
from api.v1.services.email_services import EmailService
from passlib.context import CryptContext
from typing import Optional
from api.core.settings import settings
from fastapi.templating import Jinja2Templates
from api.v1.models.user import User

templates = Jinja2Templates(directory="./api/v1/templates")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token serializer
SECRET_KEY = settings.SECRET_KEY
FRONTEND_MAGIKLINK_URL = settings.FRONTEND_MAGICLINK_URL
serializer = URLSafeTimedSerializer(SECRET_KEY)


# Helper functions
def create_reset_token(email: str) -> str:
    return serializer.dumps(email, salt=SECRET_KEY)


def verify_reset_token(token: str, expiration: int = 3600) -> Optional[str]:
    try:
        email = serializer.loads(token, salt=SECRET_KEY, max_age=expiration)
        return email
    except (BadSignature, SignatureExpired):
        return None


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


class RequestPasswordService:
    @staticmethod
    async def create(
        email: request_password_reset.RequestEmail,
        request: Request,
        session: Session,
        background_tasks: BackgroundTasks,
        url: str,
        template_file: str,
        subject: str,
    ):
        user = session.query(User).filter_by(email=email.user_email).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        token = create_reset_token(email.user_email)

        reset_link = f"{FRONTEND_MAGIKLINK_URL}{url}?token={token}"
        html_content = templates.TemplateResponse(
            f"{template_file}", {"url": reset_link, "user": user, "request": request}
        ).body.decode("utf-8")

        # Sending the email

        email_service = EmailService()
        email_subject = subject
        body = html_content

        await email_service.send_email(
            background_tasks=background_tasks,
            to_email=email.user_email,
            subject=email_subject,
            body=body,
            from_name="HNG11 Support",
        )

        # Return the success response
        return {
            "message": "Password reset link sent successfully",
            "data": {"reset_link": reset_link},
            "status_code": status.HTTP_201_CREATED,
        }

    @staticmethod
    def process_reset_link(token: str = Query(...), session: Session = Depends(get_db)):
        email = verify_reset_token(token)

        if not email:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        user = session.query(User).filter_by(email=email).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return success_response(
            message=f"token is valid for user {email}",
            status_code=status.HTTP_302_FOUND,
        )

    @staticmethod
    def verify_magic_link(token: str = Query(...), session: Session = Depends(get_db)):
        email = verify_reset_token(token)

        if not email:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        user = session.query(User).filter_by(email=email).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    @staticmethod
    def reset_password(
        data: request_password_reset.ResetPassword = Depends(),
        token: str = Query(...),
        session: Session = Depends(get_db),
    ):
        try:
            email = verify_reset_token(token)

            if not email:
                raise HTTPException(status_code=400, detail="Invalid or expired token")

            user = session.query(User).filter_by(email=email).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            if data.new_password != data.confirm_password:
                raise HTTPException(status_code=400, detail="Passwords do not match")

            user.password = get_password_hash(data.new_password)
            session.commit()

            return success_response(
                message="Password has been reset successfully",
                status_code=status.HTTP_200_OK,
            )

        except SQLAlchemyError as e:
            session.rollback()  # Rollback the session in case of an error
            print(f"Database error: {e}")  # Log the error for debugging purposes
            raise HTTPException(
                status_code=500,
                detail="An error occurred while processing your request.",
            )

    @staticmethod
    def reset_user_password(
        data: request_password_reset.ResetPassword = Depends(),
        session: Session = Depends(get_db),
        user: User = None,
    ):
        try:
            if data.new_password != data.confirm_password:
                raise HTTPException(status_code=400, detail="Passwords do not match")

            user.password = get_password_hash(data.new_password)
            session.commit()

            return success_response(
                message="Password has been reset successfully",
                status_code=status.HTTP_200_OK,
            )

        except SQLAlchemyError as e:
            session.rollback()  # Rollback the session in case of an error
            print(f"Database error: {e}")  # Log the error for debugging purposes
            raise HTTPException(
                status_code=500,
                detail="An error occurred while processing your request.",
            )


reset_service = RequestPasswordService()
