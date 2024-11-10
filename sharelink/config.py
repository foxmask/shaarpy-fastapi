# coding: utf-8
"""
2024 - ShareLink - 셰어 링크
"""
from pydantic import BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///db.sqlite3"
    LANGUAGE_CODE: str = "fr"
    SHARELINK_NAME: str = "ShareLink - 셰어 링크"
    SHARELINK_AUTHOR: str = "FoxMaSk"
    SHARELINK_DESCRIPTION: str = "Share link, thoughts, ideas and more"
    SHARELINK_ROBOT: str = "index, follow"

    SECRET_KEY: str = "itsuptousofcourse"
    COOKIE_SAMESITE: str = "none"
    COOKIE_SECURE: bool = True
    TOKEN_LOCATION: str = "body"
    TOKEN_KEY: str = "csrf-token"

    LINKS_PER_PAGE: int = 5
    DAILY_PER_PAGE: int = 10

    model_config = SettingsConfigDict(env_file=".env",
                                      env_file_encoding="utf-8",
                                      extra="ignore",)


settings = Settings()


class CsrfSettings(BaseModel):
    """
    Model to store the setting
    """
    secret_key: str = settings.SECRET_KEY
    cookie_samesite: str = settings.COOKIE_SAMESITE
    cookie_secure: bool = settings.COOKIE_SECURE
    token_location: str = settings.TOKEN_LOCATION
    token_key: str = settings.TOKEN_KEY
