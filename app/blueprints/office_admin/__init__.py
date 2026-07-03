"""
app/blueprints/office_admin/__init__.py
=======================================
Office-admin blueprint — office settings, staff management, analytics.
URL prefix: ``/office-admin``
"""

from flask import Blueprint

office_admin_bp = Blueprint(
    "office_admin",
    __name__,
    template_folder="templates",
)

from app.blueprints.office_admin import routes
