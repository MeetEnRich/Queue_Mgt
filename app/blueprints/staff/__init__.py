"""
app/blueprints/staff/__init__.py
================================
Staff blueprint — queue dashboard, call-next, complete, skip.
URL prefix: ``/staff``
"""

from flask import Blueprint

staff_bp = Blueprint(
    "staff",
    __name__,
    template_folder="templates",
)

from app.blueprints.staff import routes
