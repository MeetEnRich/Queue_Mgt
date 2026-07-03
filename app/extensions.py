"""
app/extensions.py
=================
Singleton extension instances initialised once and bound to the app in the factory.
"""

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


@login_manager.user_loader
def load_user(user_id: str):
    """Callback used by Flask-Login to reload a user from the session."""
    from app.models.staff import Staff  # deferred to avoid circular imports

    return db.session.get(Staff, int(user_id))
