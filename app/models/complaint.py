"""
app/models/complaint.py
=======================
Complaint model — the specific issue a student brings to an office.
"""

from __future__ import annotations

from datetime import datetime

from app.extensions import db


class Complaint(db.Model):
    """A complaint filed by a student at a specific office."""

    __tablename__ = "complaints"

    id: int = db.Column(db.Integer, primary_key=True)
    office_id: int = db.Column(
        db.Integer, db.ForeignKey("offices.id"), nullable=False
    )
    student_id: int = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=False
    )
    category_id: int = db.Column(
        db.Integer, db.ForeignKey("complaint_categories.id"), nullable=False
    )
    description: str = db.Column(db.Text, nullable=False)
    created_at: datetime = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )

    # ── Relationships ──────────────────────────────────────────────────
    office = db.relationship("Office", back_populates="complaints")
    student = db.relationship("Student", back_populates="complaints")
    category = db.relationship("ComplaintCategory")
    queue_token = db.relationship(
        "QueueToken", back_populates="complaint", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Complaint id={self.id} office_id={self.office_id}>"
