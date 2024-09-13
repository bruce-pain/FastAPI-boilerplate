import os
from pydantic_settings import BaseSettings
from decouple import config
from pathlib import Path


# Use this to build paths inside the project
BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """ Class to hold application's config values."""

    SECRET_KEY: str = config("SECRET_KEY")
    ALGORITHM: str = config("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = config("ACCESS_TOKEN_EXPIRE_MINUTES")
    JWT_REFRESH_EXPIRY: int = config("JWT_REFRESH_EXPIRY")

    APP_URL: str = config("APP_URL")

    MAIL_USERNAME: str = config("MAIL_USERNAME")
    MAIL_PASSWORD: str = config("MAIL_PASSWORD")
    MAIL_FROM: str = config("MAIL_FROM")
    MAIL_PORT: int = config("MAIL_PORT")
    MAIL_SERVER: str = config("MAIL_SERVER")

    # Database configurations
    DB_HOST: str = config("DB_HOST")
    DB_PORT: int = config("DB_PORT", cast=int)
    DB_USER: str = config("DB_USER")
    DB_PASSWORD: str = config("DB_PASSWORD")
    DB_NAME: str = config("DB_NAME")
    DB_TYPE: str = config("DB_TYPE")
    DB_URL: str = config("DB_URL")

    MAIL_USERNAME: str = config("MAIL_USERNAME")
    MAIL_PASSWORD: str = config("MAIL_PASSWORD")
    MAIL_FROM: str = config("MAIL_FROM")
    MAIL_PORT: int = config("MAIL_PORT")
    MAIL_SERVER: str = config("MAIL_SERVER")

    FLUTTERWAVE_SECRET: str = config("FLUTTERWAVE_SECRET")
    STRIPE_SECRET: str = config("STRIPE_SECRET")
    FLW_SECRET_HASH: str = config("FLW_SECRET_HASH")

    TWILIO_ACCOUNT_SID: str = config("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = config("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: str = config("TWILIO_PHONE_NUMBER")

    OPENAI_API_KEY: str = config("OPENAI_API_KEY")
    CELERY_BROKER_URL: str = config("CELERY_BROKER_URL")
    ASSEMBLYAI_API_KEY: str = config("ASSEMBLYAI_API_KEY")
    OPENROUTER_API_KEY: str = config("OPENROUTER_API_KEY")
    GOOEY_API_KEY: str = config("GOOEY_API_KEY")
    DEEPGRAM_API_KEY: str = config("DEEPGRAM_API_KEY")
    UNREAL_SPEECH_API_KEY: str = config("UNREAL_SPEECH_API_KEY")

    MEDIA_DIR: str = config("MEDIA_DIR")
    MAX_FILE_SIZE: int = config("MAX_FILE_SIZE")
    
    X_RAPIDAPI_KEY: str = config("X_RAPIDAPI_KEY")
    X_RAPIDAPI_HOST: str = config("X_RAPIDAPI_HOST")

    MINIO_ACCESS_KEY: str = config("MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: str = config("MINIO_SECRET_KEY")

    TEMP_DIR: str = os.path.join(Path(__file__).resolve().parent.parent.parent, 'tmp', 'media')
    STORAGE_DIR: str = os.path.join('media', 'downloads')
    FRONTEND_MAGICLINK_URL : str = config("FRONTEND_MAGICLINK_URL")
    
    @property
    def ALLOWED_EXTENSIONS(self) -> set[str]:
        raw_extensions = config("ALLOWED_EXTENSIONS", default="")
        return set(ext.strip() for ext in raw_extensions.split(",") if ext.strip())


settings = Settings()
