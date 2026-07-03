"""
app/services/analytics_service.py
=================================
Reporting / analytics helpers for office dashboards and the super-admin
university-wide overview.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import func

from app.extensions import db
from app.models.complaint import Complaint
from app.models.complaint_category import ComplaintCategory
from app.models.office import Office
from app.models.queue_token import QueueToken
from app.models.staff import Staff


def office_summary(
    office_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict[str, Any]:
    """Generate an analytics summary for a single office.

    Args:
        office_id: The office to report on.
        date_from: Start date (inclusive).  Defaults to today.
        date_to: End date (inclusive).  Defaults to today.

    Returns:
        A dict containing counts, averages, breakdowns by category / staff /
        hour, plus balk and renege proxies.
    """
    if date_from is None:
        date_from = date.today()
    if date_to is None:
        date_to = date.today()

    # Base query scope — always scoped by office
    base = QueueToken.query.filter(
        QueueToken.office_id == office_id,
        QueueToken.queue_date >= date_from,
        QueueToken.queue_date <= date_to,
    )

    # ── Counts ─────────────────────────────────────────────────────────
    total_served: int = base.filter(QueueToken.status == "completed").count()
    total_skipped: int = base.filter(QueueToken.status == "skipped").count()
    total_cancelled: int = base.filter(QueueToken.status == "cancelled").count()
    total_waiting: int = base.filter(QueueToken.status == "waiting").count()
    total_being_served: int = base.filter(QueueToken.status == "being_served").count()

    # ── Averages (completed tokens only) ───────────────────────────────
    completed = base.filter(QueueToken.status == "completed")

    avg_wait: float = (
        db.session.query(func.avg(QueueToken.wait_seconds))
        .filter(
            QueueToken.office_id == office_id,
            QueueToken.queue_date >= date_from,
            QueueToken.queue_date <= date_to,
            QueueToken.status == "completed",
            QueueToken.wait_seconds.isnot(None),
        )
        .scalar()
    ) or 0.0

    avg_service: float = (
        db.session.query(func.avg(QueueToken.service_seconds))
        .filter(
            QueueToken.office_id == office_id,
            QueueToken.queue_date >= date_from,
            QueueToken.queue_date <= date_to,
            QueueToken.status == "completed",
            QueueToken.service_seconds.isnot(None),
        )
        .scalar()
    ) or 0.0

    # ── By category ────────────────────────────────────────────────────
    by_category: list[dict[str, Any]] = []
    cat_rows = (
        db.session.query(ComplaintCategory.name, func.count(QueueToken.id))
        .join(Complaint, Complaint.id == QueueToken.complaint_id)
        .join(ComplaintCategory, ComplaintCategory.id == Complaint.category_id)
        .filter(
            QueueToken.office_id == office_id,
            QueueToken.queue_date >= date_from,
            QueueToken.queue_date <= date_to,
        )
        .group_by(ComplaintCategory.name)
        .all()
    )
    for cat_name, count in cat_rows:
        by_category.append({"name": cat_name, "count": count})

    # ── Staff leaderboard ──────────────────────────────────────────────
    staff_leaderboard: list[dict[str, Any]] = []
    staff_rows = (
        db.session.query(
            Staff.full_name,
            func.count(QueueToken.id).filter(
                QueueToken.status == "completed"
            ).label("served"),
            func.count(QueueToken.id).filter(
                QueueToken.status == "skipped"
            ).label("skipped"),
        )
        .join(Staff, Staff.id == QueueToken.assigned_staff_id)
        .filter(
            QueueToken.office_id == office_id,
            QueueToken.queue_date >= date_from,
            QueueToken.queue_date <= date_to,
        )
        .group_by(Staff.full_name)
        .order_by(func.count(QueueToken.id).filter(
            QueueToken.status == "completed"
        ).desc())
        .all()
    )
    for name, served, skipped in staff_rows:
        staff_leaderboard.append(
            {"name": name, "served": served, "skipped": skipped}
        )

    # ── Hourly arrivals ────────────────────────────────────────────────
    hourly_arrivals: list[dict[str, int]] = []
    hourly_rows = (
        db.session.query(
            func.strftime("%H", QueueToken.joined_at).label("hour"),
            func.count(QueueToken.id),
        )
        .filter(
            QueueToken.office_id == office_id,
            QueueToken.queue_date >= date_from,
            QueueToken.queue_date <= date_to,
        )
        .group_by("hour")
        .order_by("hour")
        .all()
    )
    for hour_str, count in hourly_rows:
        hourly_arrivals.append({"hour": int(hour_str), "count": count})

    # ── Balk / renege proxies ──────────────────────────────────────────
    # "balk_count" — we approximate this as total_cancelled (student left
    # before being served), since a true "turned away" event doesn't create
    # a token.  A future version could track explicit balk events.
    renege_count: int = total_cancelled

    return {
        "total_served": total_served,
        "total_skipped": total_skipped,
        "total_cancelled": total_cancelled,
        "total_waiting": total_waiting,
        "total_being_served": total_being_served,
        "avg_wait_seconds": round(avg_wait, 1),
        "avg_service_seconds": round(avg_service, 1),
        "by_category": by_category,
        "staff_leaderboard": staff_leaderboard,
        "hourly_arrivals": hourly_arrivals,
        "balk_count": 0,  # cannot track balks without explicit logging
        "renege_count": renege_count,
    }

def university_summary() -> dict[str, Any]:
    """Generate a university-wide analytics summary across all offices.

    Returns:
        A dict with per-office summaries and university-level totals.
    """
    offices = Office.query.filter_by(is_active=True).all()

    today = date.today()
    now = datetime.utcnow().time()
    office_data: list[dict[str, Any]] = []
    total_served_all = 0
    total_waiting_all = 0
    busiest_office: str | None = None
    busiest_count = 0
    worst_avg_wait: float = 0.0
    worst_wait_office: str | None = None

    for office in offices:
        summary = office_summary(office.id)
        is_open = office.office_open_time <= now <= office.office_close_time

        office_data.append(
            {
                "name": office.name,
                "slug": office.slug,
                "total_served": summary["total_served"],
                "avg_wait": summary["avg_wait_seconds"],
                "avg_service": summary["avg_service_seconds"],
                "is_open": is_open,
                "waiting": summary["total_waiting"],
                "being_served": summary["total_being_served"],
            }
        )

        total_served_all += summary["total_served"]
        total_waiting_all += summary["total_waiting"]

        if summary["total_served"] > busiest_count:
            busiest_count = summary["total_served"]
            busiest_office = office.name

        if summary["avg_wait_seconds"] > worst_avg_wait:
            worst_avg_wait = summary["avg_wait_seconds"]
            worst_wait_office = office.name

    return {
        "offices": office_data,
        "total_served_all": total_served_all,
        "total_served_today": total_served_all,
        "total_waiting": total_waiting_all,
        "busiest_office": busiest_office,
        "worst_avg_wait": round(worst_avg_wait, 1),
        "worst_avg_wait_office": worst_wait_office,
    }

