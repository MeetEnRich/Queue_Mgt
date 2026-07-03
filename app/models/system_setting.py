"""
app/models/system_setting.py
============================
Global system settings — only a single row is expected.
"""

from __future__ import annotations

from app.extensions import db


class SystemSetting(db.Model):
    """University-wide defaults for queue configuration."""

    __tablename__ = "system_settings"

    id: int = db.Column(db.Integer, primary_key=True)
    default_max_queue_capacity: int = db.Column(
        db.Integer, nullable=False, default=60
    )
    default_active_counters: int = db.Column(
        db.Integer, nullable=False, default=2
    )

    def __repr__(self) -> str:
        return (
            f"<SystemSetting capacity={self.default_max_queue_capacity} "
            f"counters={self.default_active_counters}>"
        )
