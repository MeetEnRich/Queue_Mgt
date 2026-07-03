"""
app/models/complaint_category.py
================================
Per-office complaint categories that classify why a student is visiting.
"""

from __future__ import annotations

from app.extensions import db


class ComplaintCategory(db.Model):
    """A named complaint category scoped to a single office."""

    __tablename__ = "complaint_categories"

    id: int = db.Column(db.Integer, primary_key=True)
    office_id: int = db.Column(
        db.Integer, db.ForeignKey("offices.id"), nullable=False
    )
    name: str = db.Column(db.String(60), nullable=False)
    is_active: bool = db.Column(db.Boolean, nullable=False, default=True)

    # ── Relationships ──────────────────────────────────────────────────
    office = db.relationship("Office", back_populates="complaint_categories")

    def __repr__(self) -> str:
        return f"<ComplaintCategory {self.name!r} office_id={self.office_id}>"
