"""
app/models/office.py
====================
Office model — each administrative office (e.g. Bursary, Student Affairs)
that students can queue at.
"""

from __future__ import annotations

from datetime import datetime, time

from app.extensions import db


class Office(db.Model):
    """An administrative office that operates its own independent queue."""

    __tablename__ = "offices"

    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String(100), nullable=False)
    slug: str = db.Column(db.String(30), unique=True, nullable=False, index=True)
    description: str | None = db.Column(db.String(255), nullable=True)

    max_queue_capacity: int = db.Column(db.Integer, nullable=False, default=60)
    active_counters: int = db.Column(db.Integer, nullable=False, default=2)

    office_open_time: time = db.Column(db.Time, nullable=False, default=time(8, 0))
    office_close_time: time = db.Column(db.Time, nullable=False, default=time(16, 0))

    is_active: bool = db.Column(db.Boolean, nullable=False, default=True)
    created_at: datetime = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )

    # ── Relationships ──────────────────────────────────────────────────
    staff = db.relationship(
        "Staff", back_populates="office", lazy="dynamic"
    )
    complaint_categories = db.relationship(
        "ComplaintCategory", back_populates="office", lazy="dynamic"
    )
    complaints = db.relationship(
        "Complaint", back_populates="office", lazy="dynamic"
    )
    queue_tokens = db.relationship(
        "QueueToken", back_populates="office", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Office {self.slug!r}>"
