"""User data model"""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from api.v1.models.base_model import BaseTableModel


class User(BaseTableModel):
    __tablename__ = "users"

    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)
    first_name = Column(String)
    last_name = Column(String)

    profile = relationship("Profile", back_populates="user", uselist=False)
    activity_logs = relationship("ActivityLog", back_populates="user")

    def to_dict(self):
        obj_dict = super().to_dict()
        obj_dict.pop("password")
        return obj_dict

    def __str__(self):
        return "User: {} {}".format(self.email, self.first_name)
