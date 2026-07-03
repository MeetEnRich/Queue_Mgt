"""
app/blueprints/auth/__init__.py
===============================
Authentication blueprint — login, logout.
"""

from flask import Blueprint

auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="templates",
)

from app.blueprints.auth import routes
