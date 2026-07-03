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

    # ── Geofencing Configuration ──
    GEOFENCE_ENABLED: bool = os.environ.get("GEOFENCE_ENABLED", "False").lower() in ("true", "1", "yes")
    GEOFENCE_LATITUDE: float = float(os.environ.get("GEOFENCE_LATITUDE", 8.4746))
    GEOFENCE_LONGITUDE: float = float(os.environ.get("GEOFENCE_LONGITUDE", 8.5583))
    GEOFENCE_RADIUS_METERS: float = float(os.environ.get("GEOFENCE_RADIUS_METERS", 1500.0))



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
