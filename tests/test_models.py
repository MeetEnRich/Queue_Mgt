"""
Tests for SQLAlchemy models: Office, ComplaintCategory, Student, Staff,
QueueToken, and Complaint.

Verifies field constraints, relationships, password hashing, and uniqueness.
"""

import pytest
from datetime import date, time
from app.models import Office, ComplaintCategory, Student, Staff, Complaint, QueueToken
from app.extensions import db as _db


class TestOfficeModel:
    """Tests for the Office model."""

    def test_create_office_with_all_fields(self, db):
        """An office can be created with all expected fields."""
        office = Office(
            name="Registry",
            slug="registry",
            description="Student records office",
            max_queue_capacity=40,
            active_counters=2,
            office_open_time=time(8, 0),
            office_close_time=time(16, 0),
            is_active=True,
        )
        db.session.add(office)
        db.session.commit()

        fetched = Office.query.filter_by(slug="registry").first()
        assert fetched is not None
        assert fetched.name == "Registry"
        assert fetched.slug == "registry"
        assert fetched.max_queue_capacity == 40
        assert fetched.active_counters == 2
        assert fetched.office_open_time == time(8, 0)
        assert fetched.office_close_time == time(16, 0)
        assert fetched.is_active is True

    def test_office_slug_is_unique(self, db):
        """Two offices with the same slug should raise an integrity error."""
        o1 = Office(name="Office A", slug="same-slug", max_queue_capacity=10, active_counters=1)
        o2 = Office(name="Office B", slug="same-slug", max_queue_capacity=20, active_counters=2)
        db.session.add(o1)
        db.session.commit()
        db.session.add(o2)
        with pytest.raises(Exception):
            db.session.commit()

    def test_office_has_created_at(self, db):
        """Office should have an auto-populated created_at timestamp."""
        office = Office(name="Test", slug="test-ts", max_queue_capacity=10, active_counters=1)
        db.session.add(office)
        db.session.commit()
        assert office.created_at is not None


class TestComplaintCategoryModel:
    """Tests for the ComplaintCategory model."""

    def test_category_belongs_to_office(self, sample_office, db):
        """A complaint category should be linked to an office via office_id."""
        cat = ComplaintCategory.query.filter_by(office_id=sample_office.id).first()
        assert cat is not None
        assert cat.office_id == sample_office.id

    def test_multiple_categories_per_office(self, sample_office, db):
        """An office can have multiple categories."""
        cats = ComplaintCategory.query.filter_by(office_id=sample_office.id).all()
        assert len(cats) >= 2

    def test_category_is_active_default(self, sample_office, db):
        """Categories seeded via fixtures should be active."""
        cat = ComplaintCategory.query.filter_by(office_id=sample_office.id).first()
        assert cat.is_active is True


class TestStudentModel:
    """Tests for the Student model."""

    def test_create_student(self, sample_student):
        """A student can be created with matric_no, full_name, and department."""
        assert sample_student.matric_no == "2021/CP/CSC/0295"
        assert sample_student.full_name == "Ajunwa Stephen Oche"
        assert sample_student.department == "Computer Science"

    def test_student_matric_no_is_unique(self, db):
        """Two students with the same matric_no should raise an integrity error."""
        s1 = Student(matric_no="2021/CP/CSC/0001", full_name="Student One", department="CS")
        s2 = Student(matric_no="2021/CP/CSC/0001", full_name="Student Two", department="Physics")
        db.session.add(s1)
        db.session.commit()
        db.session.add(s2)
        with pytest.raises(Exception):
            db.session.commit()

    def test_student_has_created_at(self, sample_student):
        """Student should have an auto-populated created_at timestamp."""
        assert sample_student.created_at is not None


class TestStaffModel:
    """Tests for the Staff model."""

    def test_password_hashing(self, sample_staff):
        """set_password hashes the password; check_password verifies it."""
        assert sample_staff.check_password("staff123") is True
        assert sample_staff.check_password("wrong_password") is False

    def test_password_hash_is_not_plaintext(self, sample_staff):
        """The stored password hash should not equal the plaintext password."""
        assert sample_staff.password_hash != "staff123"

    def test_staff_role_field(self, db):
        """Staff role field accepts 'staff', 'office_admin', and 'super_admin'."""
        office = Office(name="Test Office", slug="test-role", max_queue_capacity=10, active_counters=1)
        db.session.add(office)
        db.session.flush()

        for role in ["staff", "office_admin", "super_admin"]:
            s = Staff(
                office_id=office.id if role != "super_admin" else None,
                username=f"test_{role}",
                full_name=f"Test {role}",
                role=role,
            )
            s.set_password("test123")
            db.session.add(s)

        db.session.commit()
        assert Staff.query.filter_by(role="staff").first() is not None
        assert Staff.query.filter_by(role="office_admin").first() is not None
        assert Staff.query.filter_by(role="super_admin").first() is not None

    def test_staff_username_is_unique(self, sample_office, db):
        """Two staff with the same username should raise an integrity error."""
        s1 = Staff(office_id=sample_office.id, username="dup_user", full_name="One", role="staff")
        s1.set_password("pw1")
        s2 = Staff(office_id=sample_office.id, username="dup_user", full_name="Two", role="staff")
        s2.set_password("pw2")
        db.session.add(s1)
        db.session.commit()
        db.session.add(s2)
        with pytest.raises(Exception):
            db.session.commit()

    def test_super_admin_has_no_office(self, super_admin):
        """A super_admin should have office_id=None."""
        assert super_admin.office_id is None
        assert super_admin.role == "super_admin"


class TestComplaintModel:
    """Tests for the Complaint model."""

    def test_complaint_links_to_student_and_office(self, sample_office, sample_student, category_for_office_a, db):
        """A complaint is linked to a student, office, and category."""
        complaint = Complaint(
            office_id=sample_office.id,
            student_id=sample_student.id,
            category_id=category_for_office_a.id,
            description="Cannot log in to my portal.",
        )
        db.session.add(complaint)
        db.session.commit()

        fetched = Complaint.query.first()
        assert fetched.office_id == sample_office.id
        assert fetched.student_id == sample_student.id
        assert fetched.category_id == category_for_office_a.id
        assert fetched.description == "Cannot log in to my portal."

    def test_complaint_has_created_at(self, sample_office, sample_student, category_for_office_a, db):
        """Complaint should have an auto-populated created_at timestamp."""
        complaint = Complaint(
            office_id=sample_office.id,
            student_id=sample_student.id,
            category_id=category_for_office_a.id,
            description="Test complaint",
        )
        db.session.add(complaint)
        db.session.commit()
        assert complaint.created_at is not None


class TestQueueTokenModel:
    """Tests for the QueueToken model."""

    def test_create_token_with_relationships(self, sample_office, sample_student, category_for_office_a, db):
        """A QueueToken links office, student, and complaint correctly."""
        complaint = Complaint(
            office_id=sample_office.id,
            student_id=sample_student.id,
            category_id=category_for_office_a.id,
            description="Portal glitch",
        )
        db.session.add(complaint)
        db.session.flush()

        token = QueueToken(
            office_id=sample_office.id,
            token_number=1,
            queue_date=date.today(),
            student_id=sample_student.id,
            complaint_id=complaint.id,
            status="waiting",
        )
        db.session.add(token)
        db.session.commit()

        fetched = QueueToken.query.first()
        assert fetched.office_id == sample_office.id
        assert fetched.student_id == sample_student.id
        assert fetched.complaint_id == complaint.id
        assert fetched.token_number == 1
        assert fetched.status == "waiting"
        assert fetched.queue_date == date.today()

    def test_token_default_status_is_waiting(self, sample_office, sample_student, category_for_office_a, db):
        """A new token defaults to 'waiting' status."""
        complaint = Complaint(
            office_id=sample_office.id,
            student_id=sample_student.id,
            category_id=category_for_office_a.id,
            description="Test",
        )
        db.session.add(complaint)
        db.session.flush()

        token = QueueToken(
            office_id=sample_office.id,
            token_number=1,
            queue_date=date.today(),
            student_id=sample_student.id,
            complaint_id=complaint.id,
        )
        db.session.add(token)
        db.session.commit()

        assert token.status == "waiting"

    def test_token_timestamps_nullable(self, sample_office, sample_student, category_for_office_a, db):
        """called_at and completed_at should be None for a freshly created token."""
        complaint = Complaint(
            office_id=sample_office.id,
            student_id=sample_student.id,
            category_id=category_for_office_a.id,
            description="Test",
        )
        db.session.add(complaint)
        db.session.flush()

        token = QueueToken(
            office_id=sample_office.id,
            token_number=1,
            queue_date=date.today(),
            student_id=sample_student.id,
            complaint_id=complaint.id,
            status="waiting",
        )
        db.session.add(token)
        db.session.commit()

        assert token.called_at is None
        assert token.completed_at is None
        assert token.wait_seconds is None
        assert token.service_seconds is None
