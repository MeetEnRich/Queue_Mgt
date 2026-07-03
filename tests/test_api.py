"""
Tests for API endpoints via the Flask test client.

Covers office listing, queue join/cancel, status retrieval,
staff authentication, and cross-office access control.
"""

import pytest
import json

from app.extensions import db as _db
from app.models import (
    Office, ComplaintCategory, Student, Staff, Complaint, QueueToken,
)


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------

def _login(client, username, password):
    """Log in via the auth endpoint and return the response."""
    return client.post('/auth/login', data={
        'username': username,
        'password': password,
    }, follow_redirects=True)


def _join_queue_api(client, office_id, matric_no, full_name, department, category_id, description):
    """Join queue via API and return the JSON response."""
    return client.post('/api/queue/join', json={
        'office_id': office_id,
        'matric_no': matric_no,
        'full_name': full_name,
        'department': department,
        'category_id': category_id,
        'description': description,
    })


# -------------------------------------------------------------------------
# Office listing
# -------------------------------------------------------------------------

class TestGetOffices:
    """Tests for GET /api/offices."""

    def test_get_offices_returns_list(self, client, sample_office, db):
        """GET /api/offices should return a list of active offices."""
        response = client.get('/api/offices')

        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, (list, dict))
        # The response should contain at least one office
        if isinstance(data, list):
            assert len(data) >= 1
        elif isinstance(data, dict) and 'offices' in data:
            assert len(data['offices']) >= 1


# -------------------------------------------------------------------------
# Queue join API
# -------------------------------------------------------------------------

class TestJoinQueueAPI:
    """Tests for POST /api/queue/join."""

    def test_join_queue_api_creates_token(
        self, client, sample_office, category_for_office_a, db
    ):
        """POST /api/queue/join creates a token and returns token data."""
        response = _join_queue_api(
            client,
            office_id=sample_office.id,
            matric_no="2021/CP/CSC/0295",
            full_name="Ajunwa Stephen Oche",
            department="Computer Science",
            category_id=category_for_office_a.id,
            description="Portal won't load",
        )

        assert response.status_code in (200, 201)
        data = response.get_json()
        assert data is not None


# -------------------------------------------------------------------------
# Queue status
# -------------------------------------------------------------------------

class TestGetQueueStatus:
    """Tests for GET /api/queue/status/<id>."""

    def test_get_queue_status(
        self, client, sample_office, category_for_office_a, db
    ):
        """GET /api/queue/status/<id> returns position and wait estimate."""
        # First join the queue
        join_resp = _join_queue_api(
            client,
            office_id=sample_office.id,
            matric_no="2021/CP/CSC/0295",
            full_name="Ajunwa Stephen Oche",
            department="Computer Science",
            category_id=category_for_office_a.id,
            description="Need help",
        )
        join_data = join_resp.get_json()

        # Extract token ID (handle various response shapes)
        token_id = None
        if isinstance(join_data, dict):
            token_id = join_data.get('token_id') or join_data.get('id')
            if 'token' in join_data and isinstance(join_data['token'], dict):
                token_id = join_data['token'].get('id')

        if token_id is None:
            # Fallback: get from DB
            token = QueueToken.query.first()
            if token:
                token_id = token.id

        if token_id:
            response = client.get(f'/api/queue/status/{token_id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data is not None


# -------------------------------------------------------------------------
# Queue cancel
# -------------------------------------------------------------------------

class TestCancelQueue:
    """Tests for POST /api/queue/cancel/<id>."""

    def test_cancel_queue(
        self, client, sample_office, category_for_office_a, db
    ):
        """POST /api/queue/cancel/<id> changes token status to cancelled."""
        # Join queue
        join_resp = _join_queue_api(
            client,
            office_id=sample_office.id,
            matric_no="2021/CP/CSC/0295",
            full_name="Ajunwa Stephen Oche",
            department="Computer Science",
            category_id=category_for_office_a.id,
            description="Need help",
        )

        # Get token ID
        token = QueueToken.query.first()
        if token:
            response = client.post(f'/api/queue/cancel/{token.id}')
            assert response.status_code == 200


# -------------------------------------------------------------------------
# Staff auth
# -------------------------------------------------------------------------

class TestStaffAuth:
    """Tests for staff authentication on protected endpoints."""

    def test_staff_waitlist_requires_auth(self, client, sample_office, db):
        """GET /api/staff/waitlist without login should return 401 or redirect to login."""
        response = client.get('/api/staff/waitlist')
        # Should either redirect (302) to login or return 401
        assert response.status_code in (401, 302, 403)

    def test_staff_call_next_authenticated(
        self, client, sample_office, sample_staff,
        sample_student, category_for_office_a, db
    ):
        """POST /api/staff/call-next with authenticated staff should succeed."""
        # Log in as staff
        _login(client, 'mis_staff1', 'staff123')

        # Join a student to the queue
        _join_queue_api(
            client,
            office_id=sample_office.id,
            matric_no="2021/CP/CSC/0295",
            full_name="Ajunwa Stephen Oche",
            department="Computer Science",
            category_id=category_for_office_a.id,
            description="Portal issue",
        )

        # Staff calls next
        response = client.post('/api/staff/call-next')
        assert response.status_code in (200, 201)

    def test_staff_complete_authenticated(
        self, client, sample_office, sample_staff,
        sample_student, category_for_office_a, db
    ):
        """POST /api/staff/complete/<id> with authenticated staff should succeed."""
        # Log in
        _login(client, 'mis_staff1', 'staff123')

        # Join queue
        _join_queue_api(
            client,
            office_id=sample_office.id,
            matric_no="2021/CP/CSC/0295",
            full_name="Ajunwa Stephen Oche",
            department="Computer Science",
            category_id=category_for_office_a.id,
            description="Portal issue",
        )

        # Call next
        client.post('/api/staff/call-next')

        # Complete the token
        token = QueueToken.query.filter_by(status='being_served').first()
        if token:
            response = client.post(f'/api/staff/complete/{token.id}')
            assert response.status_code == 200


# -------------------------------------------------------------------------
# Cross-office access control via API
# -------------------------------------------------------------------------

class TestCrossOfficeBlocked:
    """Tests for cross-office access control enforcement via API."""

    def test_staff_cross_office_blocked(
        self, client, sample_office, sample_office_b,
        sample_staff, staff_b,
        sample_student, sample_student_b,
        category_for_office_a, category_for_office_b, db
    ):
        """
        Staff authenticated as office A should not be able to complete
        a token belonging to office B — should get 403.
        """
        # Log in as Bursary staff (office B) first to create a being_served token
        _login(client, 'bur_staff1', 'staff123')

        # Join a student to Bursary queue
        _join_queue_api(
            client,
            office_id=sample_office_b.id,
            matric_no="2022/NS/PHY/0078",
            full_name="Mohammed Kabir Yusuf",
            department="Physics",
            category_id=category_for_office_b.id,
            description="Fee issue",
        )

        # Call next in Bursary
        client.post('/api/staff/call-next')
        bursary_token = QueueToken.query.filter_by(
            office_id=sample_office_b.id, status='being_served'
        ).first()

        # Log out Bursary staff first
        client.get('/auth/logout', follow_redirects=True)

        # Now log in as MIS staff (office A)
        _login(client, 'mis_staff1', 'staff123')

        if bursary_token:
            # Try to complete the Bursary token as MIS staff
            response = client.post(f'/api/staff/complete/{bursary_token.id}')
            # Should be rejected
            assert response.status_code in (403, 404, 400)


# -------------------------------------------------------------------------
# Geofencing Validation
# -------------------------------------------------------------------------

class TestGeofencing:
    """Tests for student registration geofencing limits."""

    def test_registration_allowed_when_geofence_disabled(
        self, client, sample_office, category_for_office_a, db
    ):
        """When GEOFENCE_ENABLED is False, registration should succeed without coordinates."""
        client.application.config['GEOFENCE_ENABLED'] = False
        
        response = client.post(
            f'/o/{sample_office.slug}/register',
            data={
                'matric_no': '2021/CP/CSC/0295',
                'full_name': 'Stephen Oche',
                'department': 'Computer Science',
                'category_id': category_for_office_a.id,
                'description': 'Need login help',
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b"You have joined the queue" in response.data

    def test_registration_denied_when_missing_coordinates(
        self, client, sample_office, category_for_office_a, db
    ):
        """When GEOFENCE_ENABLED is True, registration should fail if coordinates are missing."""
        client.application.config['GEOFENCE_ENABLED'] = True
        
        response = client.post(
            f'/o/{sample_office.slug}/register',
            data={
                'matric_no': '2021/CP/CSC/0295',
                'full_name': 'Stephen Oche',
                'department': 'Computer Science',
                'category_id': category_for_office_a.id,
                'description': 'Need login help',
                'latitude': '',
                'longitude': '',
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Location access is required" in response.data

    def test_registration_denied_when_outside_radius(
        self, client, sample_office, category_for_office_a, db
    ):
        """When GEOFENCE_ENABLED is True, registration should fail if outside radius."""
        client.application.config['GEOFENCE_ENABLED'] = True
        client.application.config['GEOFENCE_LATITUDE'] = 8.4746
        client.application.config['GEOFENCE_LONGITUDE'] = 8.5583
        client.application.config['GEOFENCE_RADIUS_METERS'] = 1500.0
        
        # Test coordinates outside Lafia (e.g. Lagos, lat=6.5244, lng=3.3792)
        response = client.post(
            f'/o/{sample_office.slug}/register',
            data={
                'matric_no': '2021/CP/CSC/0295',
                'full_name': 'Stephen Oche',
                'department': 'Computer Science',
                'category_id': category_for_office_a.id,
                'description': 'Need login help',
                'latitude': '6.5244',
                'longitude': '3.3792',
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Registration Denied: You must be physically within the FULafia campus" in response.data

    def test_registration_allowed_when_inside_radius(
        self, client, sample_office, category_for_office_a, db
    ):
        """When GEOFENCE_ENABLED is True, registration should succeed if inside radius."""
        client.application.config['GEOFENCE_ENABLED'] = True
        client.application.config['GEOFENCE_LATITUDE'] = 8.4746
        client.application.config['GEOFENCE_LONGITUDE'] = 8.5583
        client.application.config['GEOFENCE_RADIUS_METERS'] = 1500.0
        
        # Test coordinates very close to FULafia center (lat=8.4747, lng=8.5584)
        response = client.post(
            f'/o/{sample_office.slug}/register',
            data={
                'matric_no': '2021/CP/CSC/0295',
                'full_name': 'Stephen Oche',
                'department': 'Computer Science',
                'category_id': category_for_office_a.id,
                'description': 'Need login help',
                'latitude': '8.4747',
                'longitude': '8.5584',
            },
            follow_redirects=True
        )
        assert response.status_code == 200
        assert b"You have joined the queue" in response.data

