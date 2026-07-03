"""
app/services/queue_service.py
=============================
Core queue operations — join, call-next, complete, skip, cancel, and status.

**Multi-office isolation is the #1 priority**: every query is scoped by
``office_id`` so that no data leaks across offices.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import func

from app.extensions import db
from app.models.complaint import Complaint
from app.models.complaint_category import ComplaintCategory
from app.models.office import Office
from app.models.queue_token import QueueToken
from app.models.staff import Staff
from app.models.student import Student
from app.utils.validators import validate_matric_no


# ── Public API ─────────────────────────────────────────────────────────


def join_queue(
    office_id: int,
    student_data: dict[str, str | None],
    complaint_data: dict[str, Any],
) -> tuple[QueueToken | None, str | None]:
    """Add a student to an office's queue.

    Args:
        office_id: The target office.
        student_data: Keys ``matric_no``, ``full_name``, ``department``,
                      ``phone_number`` (optional).
        complaint_data: Keys ``category_id``, ``description``.

    Returns:
        A ``(token, None)`` tuple on success, or ``(None, error_message)``
        on failure.
    """
    # 1. Validate the office
    office = db.session.get(Office, office_id)
    if office is None or not office.is_active:
        return None, "This office is not available at the moment."

    # 2. Validate matric number format
    matric_no: str = (student_data.get("matric_no") or "").strip().upper()
    valid, err = validate_matric_no(matric_no)
    if not valid:
        return None, err

    # 3. Validate complaint category belongs to this office
    category = db.session.get(ComplaintCategory, complaint_data.get("category_id"))
    if category is None or category.office_id != office_id or not category.is_active:
        return None, "Invalid complaint category for this office."

    # 4. Find or create the student
    student = Student.query.filter_by(matric_no=matric_no).first()
    if student is None:
        student = Student(
            matric_no=matric_no,
            full_name=student_data.get("full_name", "").strip(),
            department=student_data.get("department", "").strip(),
            phone_number=(student_data.get("phone_number") or "").strip() or None,
        )
        db.session.add(student)
        db.session.flush()  # need student.id for FK below
    else:
        # Update mutable fields on revisit
        student.full_name = student_data.get("full_name", student.full_name).strip()
        student.department = student_data.get("department", student.department).strip()
        phone = (student_data.get("phone_number") or "").strip()
        if phone:
            student.phone_number = phone

    # 5. Capacity check (balking) — scoped to this office + today
    today = date.today()
    active_count = (
        QueueToken.query
        .filter(
            QueueToken.office_id == office_id,
            QueueToken.queue_date == today,
            QueueToken.status.in_(["waiting", "being_served"]),
        )
        .count()
    )
    if active_count >= office.max_queue_capacity:
        return None, (
            "The queue is currently full. "
            f"Maximum capacity ({office.max_queue_capacity}) reached. "
            "Please try again later."
        )

    # 6. Duplicate check — student must not already be active at this office
    existing = (
        QueueToken.query
        .filter(
            QueueToken.office_id == office_id,
            QueueToken.student_id == student.id,
            QueueToken.queue_date == today,
            QueueToken.status.in_(["waiting", "being_served"]),
        )
        .first()
    )
    if existing is not None:
        return None, (
            f"You already have an active token (#{existing.token_number}) "
            "at this office today."
        )

    # 7. Create the complaint record
    complaint = Complaint(
        office_id=office_id,
        student_id=student.id,
        category_id=category.id,
        description=complaint_data.get("description", "").strip(),
    )
    db.session.add(complaint)
    db.session.flush()

    # 8. Generate the next token number for this office today
    max_token: int | None = (
        db.session.query(func.max(QueueToken.token_number))
        .filter(
            QueueToken.office_id == office_id,
            QueueToken.queue_date == today,
        )
        .scalar()
    )
    next_number = (max_token or 0) + 1

    # 9. Create the queue token
    token = QueueToken(
        office_id=office_id,
        token_number=next_number,
        queue_date=today,
        student_id=student.id,
        complaint_id=complaint.id,
        status="waiting",
    )
    db.session.add(token)
    db.session.commit()

    return token, None


def call_next(staff: Staff) -> tuple[QueueToken | None, str | None]:
    """Call the next waiting student for *staff*'s office.

    Args:
        staff: The authenticated staff member calling the next token.

    Returns:
        ``(token, None)`` on success, or ``(None, error_message)`` if the
        queue is empty or the staff has no office.
    """
    if staff.office_id is None:
        return None, "You are not assigned to any office."

    today = date.today()
    token: QueueToken | None = (
        QueueToken.query
        .filter(
            QueueToken.office_id == staff.office_id,
            QueueToken.queue_date == today,
            QueueToken.status == "waiting",
        )
        .order_by(QueueToken.joined_at.asc())
        .first()
    )
    if token is None:
        return None, "No one is waiting in the queue."

    now = datetime.utcnow()
    token.status = "being_served"
    token.assigned_staff_id = staff.id
    token.counter = staff.assigned_counter
    token.called_at = now
    token.wait_seconds = int((now - token.joined_at).total_seconds())

    db.session.commit()
    return token, None


def complete_service(
    token_id: int, staff: Staff
) -> tuple[QueueToken | None, str | None]:
    """Mark a token as completed.

    Args:
        token_id: PK of the :class:`QueueToken`.
        staff: The staff member completing the service.

    Returns:
        ``(token, None)`` on success, ``(None, error_message)`` on failure.
    """
    token = db.session.get(QueueToken, token_id)
    if token is None:
        return None, "Token not found."

    # CRITICAL: office-isolation check
    if token.office_id != staff.office_id:
        return None, "You cannot modify tokens from another office."

    if token.status != "being_served":
        return None, f"Token is not being served (current status: {token.status})."

    now = datetime.utcnow()
    token.status = "completed"
    token.completed_at = now
    if token.called_at is not None:
        token.service_seconds = int((now - token.called_at).total_seconds())

    db.session.commit()
    return token, None


def skip_token(
    token_id: int, staff: Staff
) -> tuple[QueueToken | None, str | None]:
    """Skip a token (student was absent when called).

    Args:
        token_id: PK of the :class:`QueueToken`.
        staff: The staff member skipping the token.

    Returns:
        ``(token, None)`` on success, ``(None, error_message)`` on failure.
    """
    token = db.session.get(QueueToken, token_id)
    if token is None:
        return None, "Token not found."

    if token.office_id != staff.office_id:
        return None, "You cannot modify tokens from another office."

    if token.status not in ("waiting", "being_served"):
        return None, f"Cannot skip a token with status '{token.status}'."

    token.status = "skipped"
    token.completed_at = datetime.utcnow()
    db.session.commit()
    return token, None


def cancel_token(token_id: int) -> tuple[bool, str | None]:
    """Cancel a token (student chose to leave).

    Args:
        token_id: PK of the :class:`QueueToken`.

    Returns:
        ``(True, None)`` on success, ``(False, error_message)`` on failure.
    """
    token = db.session.get(QueueToken, token_id)
    if token is None:
        return False, "Token not found."

    if token.status not in ("waiting", "being_served"):
        return False, f"Cannot cancel a token with status '{token.status}'."

    token.status = "cancelled"
    token.completed_at = datetime.utcnow()
    db.session.commit()
    return True, None


def get_queue_status(token_id: int) -> dict[str, Any] | None:
    """Return current status information for a token.

    Args:
        token_id: PK of the :class:`QueueToken`.

    Returns:
        A dict with token information, queue position, and estimated wait,
        or ``None`` if the token does not exist.
    """
    token = db.session.get(QueueToken, token_id)
    if token is None:
        return None

    position = 0
    estimated_wait = 0

    if token.status == "waiting":
        # Count how many people are ahead
        position = (
            QueueToken.query
            .filter(
                QueueToken.office_id == token.office_id,
                QueueToken.queue_date == token.queue_date,
                QueueToken.status == "waiting",
                QueueToken.joined_at < token.joined_at,
            )
            .count()
        ) + 1  # +1 for 1-based position

        from app.services.wait_time_service import estimate_wait_seconds

        estimated_wait = estimate_wait_seconds(token.office_id, position=position)

    return {
        "token_id": token.id,
        "token_number": token.token_number,
        "office_id": token.office_id,
        "status": token.status,
        "position": position,
        "estimated_wait_seconds": estimated_wait,
        "counter": token.counter,
        "joined_at": token.joined_at.isoformat() if token.joined_at else None,
        "called_at": token.called_at.isoformat() if token.called_at else None,
        "completed_at": (
            token.completed_at.isoformat() if token.completed_at else None
        ),
    }


def get_waitlist(office_id: int) -> list[QueueToken]:
    """Return all waiting tokens for an office, ordered by arrival time.

    Args:
        office_id: The office to query.

    Returns:
        A list of :class:`QueueToken` instances with ``status='waiting'``
        for today, oldest first.
    """
    today = date.today()
    return (
        QueueToken.query
        .filter(
            QueueToken.office_id == office_id,
            QueueToken.queue_date == today,
            QueueToken.status == "waiting",
        )
        .order_by(QueueToken.joined_at.asc())
        .all()
    )
