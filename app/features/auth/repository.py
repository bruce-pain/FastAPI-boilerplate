from sqlalchemy.orm import Session

from app.core.base.repository import BaseRepository
from app.features.auth.models import User


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> User:
        return self.db.query(self.model).filter(self.model.email == email).first()
