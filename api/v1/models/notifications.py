from sqlalchemy import Column, String, Text, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class Notification(BaseTableModel):
    __tablename__ = 'notifications'

    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(Enum('read', 'unread', name='notification_status'), server_default='unread')
    notification_type = Column(Enum('warning', 'info', 'success', name='notification_type'), server_default='success')
    receiver_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)

    user = relationship('User', back_populates='notifications')


class NotificationSetting(BaseTableModel):
    __tablename__ = "notification_settings"

    mobile_push_notifications = Column(Boolean, server_default='false')
    email_notification_activity_in_workspace = Column(Boolean, server_default='false')
    email_notification_always_send_email_notifications = Column(Boolean, server_default='true')
    email_notification_email_digest = Column(Boolean, server_default='false')
    email_notification_announcement_and_update_emails = Column(Boolean, server_default='false')
  

    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="notification_setting")
