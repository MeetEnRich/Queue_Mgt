"""
app/blueprints/main/__init__.py
===============================
Main (public-facing) blueprint — serves the landing page.
"""

from flask import Blueprint

main_bp = Blueprint(
    "main",
    __name__,
    template_folder="templates",
)

from app.blueprints.main import routes
