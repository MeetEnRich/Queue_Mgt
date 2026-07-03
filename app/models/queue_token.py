"""
app/models/queue_token.py
=========================
QueueToken model — each row is one student's place in an office queue.
"""

from __future__ import annotations

from datetime import datetime

from app.extensions import db


class QueueToken(db.Model):
    """A numbered token representing a student's position in a queue."""

    __tablename__ = "queue_tokens"
    __table_args__ = (
        db.Index("ix_queue_tokens_office_status", "office_id", "status"),
        db.Index("ix_queue_tokens_office_date", "office_id", "queue_date"),
    )

    id: int = db.Column(db.Integer, primary_key=True)
    office_id: int = db.Column(
        db.Integer, db.ForeignKey("offices.id"), nullable=False
    )
    token_number: int = db.Column(db.Integer, nullable=False)
    queue_date = db.Column(db.Date, nullable=False, index=True)

    student_id: int = db.Column(
        db.Integer, db.ForeignKey("students.id"), nullable=False
    )
    complaint_id: int = db.Column(
        db.Integer, db.ForeignKey("complaints.id"), nullable=False
    )

    status: str = db.Column(
        db.String(20), nullable=False, default="waiting"
    )  # waiting | being_served | completed | skipped | cancelled

    assigned_staff_id: int | None = db.Column(
        db.Integer, db.ForeignKey("staff.id"), nullable=True
    )
    counter: int | None = db.Column(db.Integer, nullable=True)

    joined_at: datetime = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )
    called_at: datetime | None = db.Column(db.DateTime, nullable=True)
    completed_at: datetime | None = db.Column(db.DateTime, nullable=True)

    wait_seconds: int | None = db.Column(db.Integer, nullable=True)
    service_seconds: int | None = db.Column(db.Integer, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────
    office = db.relationship("Office", back_populates="queue_tokens")
    student = db.relationship("Student", back_populates="queue_tokens")
    complaint = db.relationship("Complaint", back_populates="queue_token")
    assigned_staff = db.relationship("Staff", back_populates="assigned_tokens")

    def __repr__(self) -> str:
        return (
            f"<QueueToken #{self.token_number} office_id={self.office_id} "
            f"status={self.status!r}>"
        )
