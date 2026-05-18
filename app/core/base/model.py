"""This is the Base Model Class"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from uuid_extensions import uuid7

from app.core.database import Base


class BaseTableModel(Base):
    """This model creates helper methods for all models"""

    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String, primary_key=True, index=True, default=lambda: str(uuid7())
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
