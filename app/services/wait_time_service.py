"""
app/services/wait_time_service.py
=================================
Estimated-wait-time calculator using recent service history.
"""

from __future__ import annotations

from datetime import date
from math import ceil

from sqlalchemy import func

from app.extensions import db
from app.models.office import Office
from app.models.queue_token import QueueToken


def estimate_wait_seconds(
    office_id: int, position: int | None = None
) -> int:
    """Estimate the number of seconds a student at *position* will wait.

    The algorithm:
        1. Compute the average service time from the last 20 completed tokens
           at this office.
        2. Determine the number of active servers (staff who have called at
           least one token today).  Fall back to ``office.active_counters``.
        3. If *position* is not supplied, infer it from the current queue
           depth (waiting + any being_served).
        4. ``ceil(position / active_servers) * avg_service_seconds``

    Args:
        office_id: The office to estimate for.
        position: 1-based queue position.  ``None`` means "end of queue".

    Returns:
        Estimated seconds, or ``0`` when no historical data exists or the
        position is zero.
    """
    # ── Average service time from last 20 completed tokens ─────────────
    avg_service: float | None = (
        db.session.query(func.avg(QueueToken.service_seconds))
        .filter(
            QueueToken.office_id == office_id,
            QueueToken.status == "completed",
            QueueToken.service_seconds.isnot(None),
        )
        .order_by(QueueToken.completed_at.desc())
        .limit(20)
        .scalar()
    )

    if avg_service is None or avg_service <= 0:
        return 0

    # ── Active servers ─────────────────────────────────────────────────
    today = date.today()
    active_servers: int = (
        db.session.query(func.count(func.distinct(QueueToken.assigned_staff_id)))
        .filter(
            QueueToken.office_id == office_id,
            QueueToken.queue_date == today,
            QueueToken.assigned_staff_id.isnot(None),
        )
        .scalar()
    ) or 0

    if active_servers == 0:
        office = db.session.get(Office, office_id)
        active_servers = office.active_counters if office else 1

    # ── Infer position if not supplied ─────────────────────────────────
    if position is None:
        waiting_count: int = (
            QueueToken.query
            .filter(
                QueueToken.office_id == office_id,
                QueueToken.queue_date == today,
                QueueToken.status == "waiting",
            )
            .count()
        )
        being_served_count: int = (
            QueueToken.query
            .filter(
                QueueToken.office_id == office_id,
                QueueToken.queue_date == today,
                QueueToken.status == "being_served",
            )
            .count()
        )
        position = waiting_count + (1 if being_served_count > 0 else 0)

    if position <= 0:
        return 0

    return int(ceil(position / active_servers) * avg_service)
