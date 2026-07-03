"""
app/config.py
=============
Application configuration classes for development, testing, and production.
"""

import os


class BaseConfig:
    """Base configuration shared by all environments."""

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "fallback-insecure-key-change-me")
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL", "sqlite:///dqms.sqlite3"
    )


class DevelopmentConfig(BaseConfig):
    """Development-specific settings."""

    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = False


class TestingConfig(BaseConfig):
    """Testing-specific settings — uses an in-memory database."""

    TESTING: bool = True
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    WTF_CSRF_ENABLED: bool = False


class ProductionConfig(BaseConfig):
    """Production-specific settings."""

    DEBUG: bool = False


# Convenience lookup for create_app()
config_by_name: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
