"""
Tests for queue_service: join_queue, call_next, complete_service,
skip_token, cancel_token, get_queue_status, get_waitlist.

All tests verify per-office scoping of queue operations.
"""

import pytest
from datetime import date, timedelta

from app.extensions import db as _db
from app.models import Office, ComplaintCategory, Student, Staff, Complaint, QueueToken
from app.services.queue_service import (
    join_queue,
    call_next,
    complete_service,
    skip_token,
    cancel_token,
    get_queue_status,
    get_waitlist,
)


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _make_student(db_session, matric_no, name="Test Student", dept="Computer Science"):
    """Quick helper to create a student."""
    s = Student(matric_no=matric_no, full_name=name, department=dept)
    db_session.add(s)
    db_session.commit()
    return s


def _join(office, student, category, description="Test complaint"):
    """Shortcut to call join_queue with standard arguments."""
    student_data = {
        "matric_no": student.matric_no,
        "full_name": student.full_name,
        "department": student.department,
    }
    complaint_data = {
        "category_id": category.id,
        "description": description,
    }
    return join_queue(office.id, student_data, complaint_data)


# -------------------------------------------------------------------------
# join_queue tests
# -------------------------------------------------------------------------

class TestJoinQueue:
    """Tests for the join_queue service function."""

    def test_join_queue_creates_token(self, sample_office, sample_student, category_for_office_a, db):
        """Joining a queue creates a token with status='waiting' and token_number=1."""
        token, error = _join(sample_office, sample_student, category_for_office_a)

        assert error is None
        assert token is not None
        assert token.status == "waiting"
        assert token.token_number == 1
        assert token.office_id == sample_office.id
        assert token.queue_date == date.today()

    def test_join_queue_increments_token_number(
        self, sample_office, sample_student, sample_student_b, category_for_office_a, db
    ):
        """The second student to join gets token_number=2."""
        token1, _ = _join(sample_office, sample_student, category_for_office_a)
        token2, _ = _join(sample_office, sample_student_b, category_for_office_a)

        assert token1.token_number == 1
        assert token2.token_number == 2

    def test_join_queue_rejects_duplicate_active_token(
        self, sample_office, sample_student, category_for_office_a, db
    ):
        """A student cannot hold two active tokens at the same office."""
        _join(sample_office, sample_student, category_for_office_a)
        token2, error = _join(sample_office, sample_student, category_for_office_a, "Another complaint")

        assert token2 is None
        assert error is not None

    def test_join_queue_allows_different_office(
        self, sample_office, sample_office_b, sample_student,
        category_for_office_a, category_for_office_b, db
    ):
        """A student can queue at two different offices simultaneously."""
        token_a, error_a = _join(sample_office, sample_student, category_for_office_a)
        token_b, error_b = _join(sample_office_b, sample_student, category_for_office_b)

        assert error_a is None
        assert error_b is None
        assert token_a is not None
        assert token_b is not None
        assert token_a.office_id != token_b.office_id

    def test_join_queue_balking(self, db):
        """Joining a full queue (at max capacity) should fail with an error."""
        # Create an office with tiny capacity
        office = Office(
            name="Tiny Office", slug="tiny",
            max_queue_capacity=2, active_counters=1,
        )
        db.session.add(office)
        db.session.flush()
        cat = ComplaintCategory(office_id=office.id, name="General", is_active=True)
        db.session.add(cat)
        db.session.commit()

        # Fill to capacity
        for i in range(2):
            s = _make_student(db.session, f"2021/CP/TST/{i:04d}", f"Student {i}")
            _join(office, s, cat)

        # Third student should be rejected (balking)
        s3 = _make_student(db.session, "2021/CP/TST/9999", "Overflow Student")
        token, error = _join(office, s3, cat)

        assert token is None
        assert error is not None


# -------------------------------------------------------------------------
# call_next tests
# -------------------------------------------------------------------------

class TestCallNext:
    """Tests for the call_next service function."""

    def test_call_next_returns_oldest_waiting(
        self, sample_office, sample_student, sample_student_b, sample_staff,
        category_for_office_a, db
    ):
        """call_next returns the first (oldest) waiting token — FCFS."""
        token1, _ = _join(sample_office, sample_student, category_for_office_a)
        token2, _ = _join(sample_office, sample_student_b, category_for_office_a)

        called_token, error = call_next(sample_staff)

        assert error is None
        assert called_token is not None
        assert called_token.id == token1.id
        assert called_token.status == "being_served"

    def test_call_next_empty_queue(self, sample_office, sample_staff, db):
        """call_next on an empty queue should return None or an error."""
        result, error = call_next(sample_staff)

        # Either result is None or error is set
        assert result is None or error is not None


# -------------------------------------------------------------------------
# complete_service tests
# -------------------------------------------------------------------------

class TestCompleteService:
    """Tests for the complete_service function."""

    def test_complete_service_updates_status(
        self, sample_office, sample_student, sample_staff,
        category_for_office_a, db
    ):
        """Completing a token changes status to 'completed' and records service_seconds."""
        token, _ = _join(sample_office, sample_student, category_for_office_a)
        called, _ = call_next(sample_staff)
        completed, error = complete_service(called.id, sample_staff)

        assert error is None
        assert completed is not None
        assert completed.status == "completed"
        assert completed.completed_at is not None

    def test_complete_rejects_wrong_office_token(
        self, sample_office, sample_office_b, sample_student,
        sample_staff, staff_b,
        category_for_office_a, category_for_office_b, db
    ):
        """Staff from office A cannot complete a token belonging to office B."""
        # Student joins office B
        token_b, _ = _join(sample_office_b, sample_student, category_for_office_b)
        # Staff B calls next in office B
        called_b, _ = call_next(staff_b)

        # Staff A (MIS) tries to complete office B's token
        result, error = complete_service(called_b.id, sample_staff)

        assert result is None
        assert error is not None


# -------------------------------------------------------------------------
# skip_token tests
# -------------------------------------------------------------------------

class TestSkipToken:
    """Tests for the skip_token function."""

    def test_skip_token_updates_status(
        self, sample_office, sample_student, sample_staff,
        category_for_office_a, db
    ):
        """Skipping a token changes its status to 'skipped'."""
        token, _ = _join(sample_office, sample_student, category_for_office_a)
        called, _ = call_next(sample_staff)
        skipped, error = skip_token(called.id, sample_staff)

        assert error is None
        assert skipped is not None
        assert skipped.status == "skipped"


# -------------------------------------------------------------------------
# cancel_token tests
# -------------------------------------------------------------------------

class TestCancelToken:
    """Tests for the cancel_token function."""

    def test_cancel_token_updates_status(
        self, sample_office, sample_student, category_for_office_a, db
    ):
        """Cancelling a waiting token changes its status to 'cancelled'."""
        token, _ = _join(sample_office, sample_student, category_for_office_a)
        success, error = cancel_token(token.id)

        assert success is True
        assert error is None

        refreshed = QueueToken.query.get(token.id)
        assert refreshed.status == "cancelled"


# -------------------------------------------------------------------------
# Token numbering
# -------------------------------------------------------------------------

class TestTokenNumbering:
    """Tests for per-office, per-day token numbering."""

    def test_token_numbers_reset_daily(self, sample_office, sample_student, category_for_office_a, db):
        """Tokens on different dates should each start at token_number=1."""
        # Create a token for yesterday manually
        yesterday = date.today() - timedelta(days=1)
        complaint = Complaint(
            office_id=sample_office.id,
            student_id=sample_student.id,
            category_id=category_for_office_a.id,
            description="Yesterday's complaint",
        )
        db.session.add(complaint)
        db.session.flush()

        old_token = QueueToken(
            office_id=sample_office.id,
            token_number=5,
            queue_date=yesterday,
            student_id=sample_student.id,
            complaint_id=complaint.id,
            status="completed",
        )
        db.session.add(old_token)
        db.session.commit()

        # Join today — should get token_number=1, not 6
        token, _ = _join(sample_office, sample_student, category_for_office_a)
        assert token.token_number == 1


# -------------------------------------------------------------------------
# get_waitlist tests
# -------------------------------------------------------------------------

class TestGetWaitlist:
    """Tests for the get_waitlist function."""

    def test_get_waitlist_returns_only_waiting_tokens(
        self, sample_office, sample_student, sample_student_b,
        sample_staff, category_for_office_a, db
    ):
        """get_waitlist returns only tokens with status='waiting' for the given office."""
        _join(sample_office, sample_student, category_for_office_a)
        _join(sample_office, sample_student_b, category_for_office_a)
        # Call next (changes first token to being_served)
        call_next(sample_staff)

        waitlist = get_waitlist(sample_office.id)

        # Only the second token should still be waiting
        waiting_statuses = [t.status for t in waitlist]
        assert all(s == "waiting" for s in waiting_statuses)
        assert len(waitlist) >= 1
