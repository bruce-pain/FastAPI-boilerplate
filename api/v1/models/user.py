"""User data model"""

from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel
from datetime import datetime, timedelta, timezone


class User(BaseTableModel):
    __tablename__ = "users"

    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)
    first_name = Column(String)
    last_name = Column(String)
    avatar_url = Column(String)
    is_active = Column(Boolean, server_default="true")
    is_superadmin = Column(Boolean, server_default="false")
    is_deleted = Column(Boolean, server_default="false")

    last_login = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("Profile", back_populates="user", uselist=False)
    notifications = relationship("Notification", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="user")
    subscription = relationship("UserSubscription", uselist=False)
    payments = relationship("Payment", back_populates="user")
    projects = relationship("Project", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    notification_setting = relationship("NotificationSetting", back_populates="user")
    data_privacy_setting = relationship(
        "DataPrivacySetting", back_populates="user", uselist=False
    )
    lang_reg_timezone_settings = relationship(
        "LanguageRegionTimezoneSetting", back_populates="user"
    )
    jobs = relationship("Job", back_populates="user")
    tool_usage = relationship('UserUsageStore', back_populates='user')
    
    def to_dict(self):
        obj_dict = super().to_dict()
        obj_dict.pop("password")
        if self.last_login:
            obj_dict["last_login"] = self.last_login.isoformat()
        return obj_dict

    def update_last_login(self):
        """
        Update the user's last login field
        """
        self.last_login = datetime.now(timezone(timedelta(hours=1)))

    def update_active_status(self):
        """update active based on last_login"""

        # check if last_login is not None or null
        if self.last_login and isinstance(self.last_login, datetime):
            current_time = datetime.now(timezone(timedelta(hours=1)))
            one_hour_ago = current_time - timedelta(hours=1)

            if self.last_login.tzinfo is None:
                self.last_login = self.last_login.replace(
                    tzinfo=timezone(timedelta(hours=1))
                )

            self.is_active = self.last_login >= one_hour_ago

    def __str__(self):
        return self.email