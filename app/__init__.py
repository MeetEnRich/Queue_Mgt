"""
app/__init__.py
===============
Application factory for the FULafia Digital Queue Management System.
"""

from __future__ import annotations

import os

from flask import Flask, render_template

from app.config import config_by_name
from app.extensions import csrf, db, login_manager, migrate


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_name: One of ``'development'``, ``'testing'``, or ``'production'``.
                     Defaults to the ``FLASK_ENV`` environment variable or
                     ``'development'``.

    Returns:
        A fully configured :class:`~flask.Flask` instance.
    """
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name[config_name])

    # Ensure the instance directory exists (for SQLite)
    os.makedirs(app.instance_path, exist_ok=True)

    # ── Initialise extensions ──────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"  # type: ignore[assignment]
    login_manager.login_message_category = "warning"

    # ── Register blueprints ────────────────────────────────────────────
    _register_blueprints(app)

    # ── Register error handlers ────────────────────────────────────────
    _register_error_handlers(app)

    return app


# ── Private helpers ────────────────────────────────────────────────────


def _register_blueprints(app: Flask) -> None:
    """Import and register all seven application blueprints."""
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.student import student_bp
    from app.blueprints.staff import staff_bp
    from app.blueprints.office_admin import office_admin_bp
    from app.blueprints.super_admin import super_admin_bp
    from app.blueprints.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(student_bp, url_prefix="/o")
    app.register_blueprint(staff_bp, url_prefix="/staff")
    app.register_blueprint(office_admin_bp, url_prefix="/office-admin")
    app.register_blueprint(super_admin_bp, url_prefix="/super-admin")
    app.register_blueprint(api_bp, url_prefix="/api")


def _register_error_handlers(app: Flask) -> None:
    """Register friendly HTML error pages."""

    @app.errorhandler(404)
    def page_not_found(error):  # noqa: ARG001
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):  # noqa: ARG001
        return render_template("errors/500.html"), 500
