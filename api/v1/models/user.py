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
    is_superadmin = Column(Boolean, server_default="false")
    is_deleted = Column(Boolean, server_default="false")

    profile = relationship("Profile", back_populates="user", uselist=False)
    activity_logs = relationship("ActivityLog", back_populates="user")

    def to_dict(self):
        obj_dict = super().to_dict()
        obj_dict.pop("password")
        if self.last_login:
            obj_dict["last_login"] = self.last_login.isoformat()
        return obj_dict

    def __str__(self):
        return self.email
