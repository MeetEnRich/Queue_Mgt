"""
app/models/staff.py
===================
Staff model — login-capable users (staff, office_admin, super_admin).
Implements :class:`flask_login.UserMixin` for session management.
"""

from __future__ import annotations

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class Staff(UserMixin, db.Model):
    """An authenticated staff member who can process queue tokens."""

    __tablename__ = "staff"

    id: int = db.Column(db.Integer, primary_key=True)
    office_id: int | None = db.Column(
        db.Integer, db.ForeignKey("offices.id"), nullable=True
    )
    username: str = db.Column(db.String(50), unique=True, nullable=False)
    password_hash: str = db.Column(db.String(255), nullable=False)
    full_name: str = db.Column(db.String(120), nullable=False)
    role: str = db.Column(
        db.String(15), nullable=False, default="staff"
    )  # staff | office_admin | super_admin
    assigned_counter: int | None = db.Column(db.Integer, nullable=True)
    is_active: bool = db.Column(db.Boolean, nullable=False, default=True)
    created_at: datetime = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )

    # ── Relationships ──────────────────────────────────────────────────
    office = db.relationship("Office", back_populates="staff")
    assigned_tokens = db.relationship(
        "QueueToken", back_populates="assigned_staff", lazy="dynamic"
    )

    # ── Password helpers ───────────────────────────────────────────────

    def set_password(self, password: str) -> None:
        """Hash and store *password*."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Return ``True`` if *password* matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<Staff {self.username!r} role={self.role!r}>"
