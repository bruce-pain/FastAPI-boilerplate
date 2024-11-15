"""User data model"""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.core.base.model import BaseTableModel


class User(BaseTableModel):
    __tablename__ = "users"

    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)
    first_name = Column(String)
    last_name = Column(String)

    def to_dict(self):
        obj_dict = super().to_dict()
        obj_dict.pop("password")
        return obj_dict

    def __str__(self):
        return "User: {} {}".format(self.email, self.first_name)