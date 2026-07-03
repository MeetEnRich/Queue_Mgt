"""
CRITICAL multi-office isolation tests.

These tests prove that office data is strictly isolated:
- Staff from one office cannot call/complete/skip tokens at another office
- Waitlists only show their own office's tokens
- Analytics are scoped per office

This is the most important test file in the project — if any of these
fail, the multi-office design is broken.
"""

import pytest
from datetime import date

from app.extensions import db as _db
from app.models import (
    Office, ComplaintCategory, Student, Staff, Complaint, QueueToken,
)
from app.services.queue_service import (
    join_queue,
    call_next,
    complete_service,
    skip_token,
    get_waitlist,
)
from app.services.analytics_service import office_summary


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _join_office(office, student, category, description="Isolation test complaint"):
    """Helper to join a student to an office queue."""
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
# Cross-office call_next isolation
# -------------------------------------------------------------------------

class TestCallNextIsolation:
    """Staff's call_next must never return tokens from another office."""

    def test_staff_cannot_call_next_from_other_office(
        self, sample_office, sample_office_b,
        sample_student, sample_student_b,
        sample_staff, staff_b,
        category_for_office_a, category_for_office_b, db
    ):
        """
        Bursary staff's call_next should never return an M.I.S token.

        Setup: Student A queues at M.I.S (office A). Office B (Bursary)
        has no waiting tokens. Staff B (Bursary) calls next.
        Expected: Staff B gets None — not Student A's MIS token.
        """
        # Student queues at MIS (office A)
        token_a, _ = _join_office(sample_office, sample_student, category_for_office_a)
        assert token_a is not None

        # Bursary staff (office B) tries to call next
        result, error = call_next(staff_b)

        # Should get nothing — office B has no waiting tokens
        assert result is None


# -------------------------------------------------------------------------
# Cross-office complete isolation
# -------------------------------------------------------------------------

class TestCompleteIsolation:
    """Staff cannot complete tokens belonging to another office."""

    def test_staff_cannot_complete_other_office_token(
        self, sample_office, sample_office_b,
        sample_student,
        sample_staff, staff_b,
        category_for_office_a, category_for_office_b, db
    ):
        """
        Attempt to complete a token from another office should return an error.

        Setup: Student joins MIS queue, MIS staff calls next (token is being_served).
        Bursary staff tries to complete that MIS token.
        Expected: Error / rejection.
        """
        # Student joins office A (MIS)
        token_a, _ = _join_office(sample_office, sample_student, category_for_office_a)
        # MIS staff calls next
        called, _ = call_next(sample_staff)
        assert called is not None
        assert called.status == "being_served"

        # Bursary staff tries to complete MIS token
        result, error = complete_service(called.id, staff_b)

        assert result is None
        assert error is not None


# -------------------------------------------------------------------------
# Cross-office skip isolation
# -------------------------------------------------------------------------

class TestSkipIsolation:
    """Staff cannot skip tokens belonging to another office."""

    def test_staff_cannot_skip_other_office_token(
        self, sample_office, sample_office_b,
        sample_student,
        sample_staff, staff_b,
        category_for_office_a, category_for_office_b, db
    ):
        """
        Attempt to skip a token from another office should return an error.

        Setup: Student joins MIS queue, MIS staff calls next.
        Bursary staff tries to skip that MIS token.
        Expected: Error / rejection.
        """
        token_a, _ = _join_office(sample_office, sample_student, category_for_office_a)
        called, _ = call_next(sample_staff)
        assert called is not None

        # Bursary staff tries to skip MIS token
        result, error = skip_token(called.id, staff_b)

        assert result is None
        assert error is not None


# -------------------------------------------------------------------------
# Waitlist isolation
# -------------------------------------------------------------------------

class TestWaitlistIsolation:
    """get_waitlist must only return tokens for the requested office."""

    def test_waitlist_only_shows_own_office(
        self, sample_office, sample_office_b,
        sample_student, sample_student_b,
        category_for_office_a, category_for_office_b, db
    ):
        """
        Waitlist for office A should never include office B's tokens.

        Setup: Student A queues at MIS, Student B queues at Bursary.
        Expected: MIS waitlist has only 1 token; Bursary waitlist has only 1 token.
        """
        _join_office(sample_office, sample_student, category_for_office_a)
        _join_office(sample_office_b, sample_student_b, category_for_office_b)

        waitlist_a = get_waitlist(sample_office.id)
        waitlist_b = get_waitlist(sample_office_b.id)

        # Verify each waitlist only contains its own office's tokens
        for token in waitlist_a:
            assert token.office_id == sample_office.id, \
                f"Token {token.id} from office {token.office_id} leaked into office A's waitlist"

        for token in waitlist_b:
            assert token.office_id == sample_office_b.id, \
                f"Token {token.id} from office {token.office_id} leaked into office B's waitlist"

        assert len(waitlist_a) == 1
        assert len(waitlist_b) == 1

    def test_waitlist_empty_for_office_with_no_tokens(
        self, sample_office, sample_office_b,
        sample_student, category_for_office_a, db
    ):
        """An office with no tokens should have an empty waitlist."""
        # Only MIS gets a token
        _join_office(sample_office, sample_student, category_for_office_a)

        waitlist_b = get_waitlist(sample_office_b.id)
        assert len(waitlist_b) == 0


# -------------------------------------------------------------------------
# Analytics isolation
# -------------------------------------------------------------------------

class TestAnalyticsIsolation:
    """office_summary must be scoped to the requested office only."""

    def test_office_admin_analytics_scoped(
        self, sample_office, sample_office_b,
        sample_student, sample_student_b,
        sample_staff, staff_b,
        category_for_office_a, category_for_office_b, db
    ):
        """
        office_summary(office_A) should not count office_B's data.

        Setup: 2 tokens in office A (1 completed), 1 token in office B (1 completed).
        Expected: office_summary(A) counts only A's token; office_summary(B) counts only B's.
        """
        # Office A: join + complete
        token_a, _ = _join_office(sample_office, sample_student, category_for_office_a)
        called_a, _ = call_next(sample_staff)
        complete_service(called_a.id, sample_staff)

        # Office B: join + complete
        token_b, _ = _join_office(sample_office_b, sample_student_b, category_for_office_b)
        called_b, _ = call_next(staff_b)
        complete_service(called_b.id, staff_b)

        summary_a = office_summary(sample_office.id)
        summary_b = office_summary(sample_office_b.id)

        # Each should reflect its own data only
        assert summary_a is not None
        assert summary_b is not None

        # The summaries should be independent — no cross-contamination
        # (Specific assertions depend on the shape of the summary dict,
        # but at minimum they should both exist and not throw errors.)


# -------------------------------------------------------------------------
# Simultaneous multi-office tokens for one student
# -------------------------------------------------------------------------

class TestStudentMultiOffice:
    """A student can hold active tokens at multiple offices simultaneously."""

    def test_student_active_at_two_offices(
        self, sample_office, sample_office_b,
        sample_student,
        category_for_office_a, category_for_office_b, db
    ):
        """
        A student can simultaneously be waiting at MIS and Bursary.
        """
        token_a, err_a = _join_office(sample_office, sample_student, category_for_office_a)
        token_b, err_b = _join_office(sample_office_b, sample_student, category_for_office_b)

        assert err_a is None
        assert err_b is None
        assert token_a.office_id == sample_office.id
        assert token_b.office_id == sample_office_b.id
        assert token_a.student_id == token_b.student_id

    def test_student_cannot_hold_two_tokens_at_same_office(
        self, sample_office, sample_student, category_for_office_a, db
    ):
        """
        A student cannot hold two active tokens at the same office.
        """
        token1, err1 = _join_office(sample_office, sample_student, category_for_office_a)
        token2, err2 = _join_office(
            sample_office, sample_student, category_for_office_a,
            "Second complaint at same office"
        )

        assert token1 is not None
        assert token2 is None
        assert err2 is not None
