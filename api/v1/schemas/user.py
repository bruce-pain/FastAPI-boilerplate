import re
from datetime import datetime
from typing import Optional, Union, List, Annotated

from pydantic import (
    BaseModel,
    EmailStr,
    ConfigDict,
    StringConstraints,
)


class UserBase(BaseModel):
    """Base user schema"""

    id: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: EmailStr
    avatar_url: Optional[str] = None
    created_at: datetime


class UserCreate(BaseModel):
    """Schema to create a user"""

    email: EmailStr
    password: Annotated[
        str, StringConstraints(min_length=3, max_length=64, strip_whitespace=True)
    ]
    first_name: Annotated[
        str, StringConstraints(min_length=2, max_length=30, strip_whitespace=True)
    ]
    last_name: Annotated[
        str, StringConstraints(min_length=2, max_length=30, strip_whitespace=True)
    ]


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None


class UserData(BaseModel):
    """
    Schema for users to be returned to superadmin
    """

    id: str
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    is_deleted: bool
    is_superadmin: bool
    created_at: datetime
    updated_at: datetime
    last_login: Union[datetime, None]

    model_config = ConfigDict(from_attributes=True)


class UserDetailData(UserData):
    most_used_tool: str


class UserDetailResponse(BaseModel):
    status: str
    message: str
    data: UserDetailData
    status_code: int


class AllUsersResponse(BaseModel):
    """
    Schema for all users
    """

    message: str
    status_code: int
    status: str
    page: int
    per_page: int
    total_pages: int
    total: int
    data: Union[List[UserData], List[None]]


class AdminCreateUser(BaseModel):
    """
    Schema for admin to create a users
    """

    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    password: str = ""
    is_active: bool = False
    is_deleted: bool = False
    is_verified: bool = False
    is_superadmin: bool = False

    model_config = ConfigDict(from_attributes=True)


class AdminCreateUserResponse(BaseModel):
    """
    Schema response for user created by admin
    """

    message: str
    status_code: int
    status: str
    data: UserData


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class EmailRequest(BaseModel):
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema to structure token data"""

    id: Optional[str]


class DeactivateUserSchema(BaseModel):
    """Schema for deactivating a user"""

    reason: Optional[str] = None
    confirmation: bool


class ChangePasswordSchema(BaseModel):
    """Schema for changing password of a user"""

    old_password: str
    new_password: str
    confirm_new_password: str


class UserStatResponse(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    deleted: int
    created_in_last_hour: int
    active_in_last_hour: int
    inactive_in_last_hour: int
    deleted_in_last_hour: int


class UserRestoreResponse(BaseModel):
    status: str
    message: str
    status_code: int


class UserActivityData(BaseModel):
    id: str
    created_at: datetime
    tool_used: str
    status: str


class UserActivityStatisticsResponse(BaseModel):
    status: str
    message: str
    total_jobs_created: int
    total_jobs_retrieved: int
    total_jobs_completed: int
    total_jobs_pending: int
    total_jobs_in_progress: int
    status_code: int


class UserActivityResponse(BaseModel):
    status: str
    message: str
    page: int
    per_page: int
    total_jobs_retrieved: int
    total_pages: int
    data: Union[List[UserActivityData], List[None]]
    status_code: int


class UserUpdateResponseData(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    last_login: Union[datetime, None]


class UserUpdateResponse(BaseModel):
    status: str = "success"
    message: str = "User Updated Successfully"
    data: UserUpdateResponseData
    status_code: int = 200


class RegisterUserData(BaseModel):
    """Registration schema"""

    id: str
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    is_superadmin: bool
    created_at: datetime
    last_login: Union[datetime, None]


class RegisterUserResponse(BaseModel):
    status: str
    status_code: int
    message: str
    access_token: str
    data: RegisterUserData

class CurrentUserDetailResponse(BaseModel):
    status: str
    status_code: int
    message: str
    data: RegisterUserData


class RefreshAccessTokenResponse(BaseModel):
    status: str
    status_code: int
    message: str
    data: Token

class LogoutResponse(BaseModel):
    status: str = "success"
    status_code: int = 200
    message: str

class MagicLinkData(BaseModel):
    magic_link: str

class MagicLinkResponse(BaseModel):
    status: str
    status_code: int
    message: str
    data: MagicLinkData
