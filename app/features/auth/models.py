"""User data model"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base.model import BaseTableModel


class User(BaseTableModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=True)

    def __str__(self):
        return "User: {}".format(self.email)

