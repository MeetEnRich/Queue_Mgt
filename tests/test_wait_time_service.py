"""
Tests for wait_time_service: estimate_wait_seconds.

Verifies that wait time estimation works correctly with
no history, with completed tokens, and independently per office.
"""

import pytest
from datetime import date, datetime, timedelta

from app.extensions import db as _db
from app.models import Office, ComplaintCategory, Student, Complaint, QueueToken
from app.services.wait_time_service import estimate_wait_seconds


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _create_completed_token(db_session, office, student, category, service_seconds, token_number=1):
    """Create a completed token with a known service_seconds value."""
    complaint = Complaint(
        office_id=office.id,
        student_id=student.id,
        category_id=category.id,
        description="Test complaint",
    )
    db_session.add(complaint)
    db_session.flush()

    now = datetime.utcnow()
    token = QueueToken(
        office_id=office.id,
        token_number=token_number,
        queue_date=date.today(),
        student_id=student.id,
        complaint_id=complaint.id,
        status="completed",
        joined_at=now - timedelta(seconds=service_seconds + 60),
        called_at=now - timedelta(seconds=service_seconds),
        completed_at=now,
        wait_seconds=60,
        service_seconds=service_seconds,
    )
    db_session.add(token)
    db_session.commit()
    return token


# -------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------

class TestEstimateWaitSeconds:
    """Tests for the estimate_wait_seconds function."""

    def test_estimate_with_no_history(self, sample_office, db):
        """With no completed tokens, estimate should return 0 or a reasonable default."""
        result = estimate_wait_seconds(sample_office.id, position=1)

        # Should not raise and should return a non-negative integer
        assert isinstance(result, (int, float))
        assert result >= 0

    def test_estimate_with_completed_tokens(
        self, sample_office, sample_student, sample_student_b,
        category_for_office_a, db
    ):
        """With completed tokens, estimate should be calculated from average service time."""
        # Create several completed tokens with known service_seconds
        students = [sample_student, sample_student_b]
        service_times = [300, 600]  # 5 min and 10 min → avg = 450s

        for i, (student, svc_time) in enumerate(zip(students, service_times)):
            _create_completed_token(
                db.session, sample_office, student,
                category_for_office_a, svc_time, token_number=i + 1,
            )

        result = estimate_wait_seconds(sample_office.id, position=1)

        # With data, estimate should be positive
        assert result > 0

    def test_estimate_independent_per_office(
        self, sample_office, sample_office_b,
        sample_student, sample_student_b,
        category_for_office_a, category_for_office_b, db
    ):
        """Two offices with different histories should give different estimates."""
        # Office A: fast service (120s avg)
        _create_completed_token(
            db.session, sample_office, sample_student,
            category_for_office_a, 120, token_number=1,
        )

        # Office B: slow service (900s avg)
        _create_completed_token(
            db.session, sample_office_b, sample_student_b,
            category_for_office_b, 900, token_number=1,
        )

        est_a = estimate_wait_seconds(sample_office.id, position=2)
        est_b = estimate_wait_seconds(sample_office_b.id, position=2)

        # Office B should have a higher estimate than A (same position but slower service)
        assert est_b > est_a

    def test_estimate_increases_with_position(
        self, sample_office, sample_student, category_for_office_a, db
    ):
        """Higher position in queue should yield a higher estimated wait."""
        _create_completed_token(
            db.session, sample_office, sample_student,
            category_for_office_a, 300, token_number=1,
        )

        est_pos_1 = estimate_wait_seconds(sample_office.id, position=1)
        est_pos_5 = estimate_wait_seconds(sample_office.id, position=5)

        assert est_pos_5 >= est_pos_1
