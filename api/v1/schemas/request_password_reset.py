from pydantic import BaseModel, EmailStr, Field


class RequestEmail(BaseModel):
    user_email: EmailStr


class ResetPassword(BaseModel):
    new_password: str = Field(min_length=3)
    confirm_password: str = Field(min_length=3)


class ResetPasswordResponse(BaseModel):
    status_code: int
    success: bool
    message: str
