"""
app/blueprints/api/__init__.py
==============================
REST API blueprint — JSON endpoints for AJAX / real-time updates.
URL prefix: ``/api``
"""

from flask import Blueprint

api_bp = Blueprint(
    "api",
    __name__,
)

from app.blueprints.api import routes
