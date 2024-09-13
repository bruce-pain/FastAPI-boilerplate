"""The database module"""

from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy import create_engine
from api.core.config import config, BASE_DIR


DB_HOST = config.DB_HOST
DB_PORT = config.DB_PORT
DB_USER = config.DB_USER
DB_PASSWORD = config.DB_PASSWORD
DB_NAME = config.DB_NAME
DB_TYPE = config.DB_TYPE


def get_db_engine(test_mode: bool = False):
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    if DB_TYPE == "sqlite" or test_mode:
        BASE_PATH = f"sqlite:///{BASE_DIR}"
        DATABASE_URL = BASE_PATH + "/"

        if test_mode:
            DATABASE_URL = BASE_PATH + "test.db"

            return create_engine(
                DATABASE_URL, connect_args={"check_same_thread": False}
            )
    elif DB_TYPE == "postgresql":
        DATABASE_URL = (
            f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    return create_engine(DATABASE_URL)


engine = get_db_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db_session = scoped_session(SessionLocal)

Base = declarative_base()


def create_database():
    return Base.metadata.create_all(bind=engine)


def get_db():
    db = db_session()
    try:
        yield db
    finally:
        db.close()
