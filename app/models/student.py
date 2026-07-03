"""
app/models/student.py
=====================
Student model — identified by their matric number.
"""

from __future__ import annotations

from datetime import datetime

from app.extensions import db


class Student(db.Model):
    """A university student who can join office queues."""

    __tablename__ = "students"

    id: int = db.Column(db.Integer, primary_key=True)
    matric_no: str = db.Column(
        db.String(20), unique=True, nullable=False, index=True
    )
    full_name: str = db.Column(db.String(120), nullable=False)
    department: str = db.Column(db.String(80), nullable=False)
    phone_number: str | None = db.Column(db.String(20), nullable=True)

    created_at: datetime = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )

    # ── Relationships ──────────────────────────────────────────────────
    complaints = db.relationship(
        "Complaint", back_populates="student", lazy="dynamic"
    )
    queue_tokens = db.relationship(
        "QueueToken", back_populates="student", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Student {self.matric_no!r}>"
