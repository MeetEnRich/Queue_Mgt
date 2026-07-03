"""
Pytest configuration and shared fixtures for FULafia DQMS test suite.

Provides:
- In-memory SQLite test database
- Flask test client
- Sample office, student, staff fixtures for test isolation
"""

import pytest
from datetime import time

from app import create_app
from app.extensions import db as _db
from app.models import Office, ComplaintCategory, Student, Staff, Complaint, QueueToken


# -------------------------------------------------------------------------
# App & DB fixtures
# -------------------------------------------------------------------------

@pytest.fixture(scope='session')
def app():
    """Create the Flask application configured for testing."""
    app = create_app('testing')
    app.config['SERVER_NAME'] = 'localhost'
    return app


@pytest.fixture(scope='function')
def db(app):
    """
    Provide a clean database for each test function.

    Creates all tables before the test and drops them after,
    ensuring complete isolation between tests.
    """
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture
def client(app, db):
    """Flask test client with a clean database."""
    return app.test_client()


# -------------------------------------------------------------------------
# Sample Office fixtures
# -------------------------------------------------------------------------

@pytest.fixture
def sample_office(db):
    """
    Create a test office (M.I.S) with 3 complaint categories.

    Returns the Office instance with id available.
    """
    office = Office(
        name="Management Information System (M.I.S/ICT)",
        slug="mis",
        description="Test MIS office",
        max_queue_capacity=50,
        active_counters=3,
        office_open_time=time(8, 0),
        office_close_time=time(16, 0),
        is_active=True,
    )
    db.session.add(office)
    db.session.flush()

    categories = [
        ComplaintCategory(office_id=office.id, name="Portal Login Issue", is_active=True),
        ComplaintCategory(office_id=office.id, name="Payment Verification Error", is_active=True),
        ComplaintCategory(office_id=office.id, name="Other", is_active=True),
    ]
    for cat in categories:
        db.session.add(cat)
    db.session.commit()

    return office


@pytest.fixture
def sample_office_b(db):
    """
    Create a SECOND test office (Bursary) for cross-office isolation tests.

    Returns the Office instance with id available.
    """
    office = Office(
        name="Bursary",
        slug="bursary",
        description="Test Bursary office",
        max_queue_capacity=60,
        active_counters=3,
        office_open_time=time(8, 0),
        office_close_time=time(15, 0),
        is_active=True,
    )
    db.session.add(office)
    db.session.flush()

    categories = [
        ComplaintCategory(office_id=office.id, name="Fee Payment Discrepancy", is_active=True),
        ComplaintCategory(office_id=office.id, name="Other", is_active=True),
    ]
    for cat in categories:
        db.session.add(cat)
    db.session.commit()

    return office


# -------------------------------------------------------------------------
# Sample Student fixtures
# -------------------------------------------------------------------------

@pytest.fixture
def sample_student(db):
    """Create a single test student."""
    student = Student(
        matric_no="2021/CP/CSC/0295",
        full_name="Ajunwa Stephen Oche",
        department="Computer Science",
    )
    db.session.add(student)
    db.session.commit()
    return student


@pytest.fixture
def sample_student_b(db):
    """Create a second test student for multi-student tests."""
    student = Student(
        matric_no="2022/NS/PHY/0078",
        full_name="Mohammed Kabir Yusuf",
        department="Physics",
    )
    db.session.add(student)
    db.session.commit()
    return student


@pytest.fixture
def sample_student_c(db):
    """Create a third test student."""
    student = Student(
        matric_no="2020/AR/PHY/0055",
        full_name="Ngozi Adaeze Nwosu",
        department="Physics",
    )
    db.session.add(student)
    db.session.commit()
    return student


# -------------------------------------------------------------------------
# Sample Staff fixtures
# -------------------------------------------------------------------------

@pytest.fixture
def sample_staff(sample_office, db):
    """Create a staff member assigned to sample_office (M.I.S)."""
    staff = Staff(
        office_id=sample_office.id,
        username="mis_staff1",
        full_name="Mr. Yusuf Abdullahi",
        role="staff",
        assigned_counter=1,
        is_active=True,
    )
    staff.set_password("staff123")
    db.session.add(staff)
    db.session.commit()
    return staff


@pytest.fixture
def sample_admin(sample_office, db):
    """Create an office_admin assigned to sample_office (M.I.S)."""
    admin = Staff(
        office_id=sample_office.id,
        username="mis_admin",
        full_name="Mrs. Hauwa Garba",
        role="office_admin",
        assigned_counter=None,
        is_active=True,
    )
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def staff_b(sample_office_b, db):
    """Create a staff member assigned to sample_office_b (Bursary)."""
    staff = Staff(
        office_id=sample_office_b.id,
        username="bur_staff1",
        full_name="Mrs. Amina Mohammed",
        role="staff",
        assigned_counter=1,
        is_active=True,
    )
    staff.set_password("staff123")
    db.session.add(staff)
    db.session.commit()
    return staff


@pytest.fixture
def super_admin(db):
    """Create a super_admin account (no office)."""
    admin = Staff(
        office_id=None,
        username="superadmin",
        full_name="Prof. Ibrahim Bello",
        role="super_admin",
        assigned_counter=None,
        is_active=True,
    )
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    return admin


# -------------------------------------------------------------------------
# Helper: get first category for an office
# -------------------------------------------------------------------------

@pytest.fixture
def category_for_office_a(sample_office, db):
    """Return the first complaint category for sample_office."""
    return ComplaintCategory.query.filter_by(office_id=sample_office.id).first()


@pytest.fixture
def category_for_office_b(sample_office_b, db):
    """Return the first complaint category for sample_office_b."""
    return ComplaintCategory.query.filter_by(office_id=sample_office_b.id).first()
