from pydantic import BaseModel
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class NotificationStatusEnum(str, Enum):
    READ = 'read'
    UNREAD = 'unread'

class NotificationTypeEnum(str, Enum):
    WARNING = 'warning'
    INFO = 'info'
    SUCCESS = 'success'


class RetrieveNotificationSchema(BaseModel):
    """Base schema for Testimonials"""

    id: str
    title: str
    message: str
    status: NotificationStatusEnum = NotificationStatusEnum.UNREAD
    notification_type: NotificationTypeEnum = NotificationTypeEnum.SUCCESS
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True