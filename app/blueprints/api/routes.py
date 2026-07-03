from flask import jsonify, request
from flask_login import current_user, login_required

from app.blueprints.api import api_bp
from app.models import Office, QueueToken
from app.services.queue_service import (
    join_queue, call_next, complete_service, skip_token,
    cancel_token, get_queue_status, get_waitlist,
)
from app.services.analytics_service import office_summary, university_summary
from app.utils.decorators import role_required
from app.extensions import db


# ------------------------------------------------------------------
# Public endpoints
# ------------------------------------------------------------------

@api_bp.route('/offices', methods=['GET'])
def list_offices():
    """Return all active offices as JSON."""
    offices = Office.query.filter_by(is_active=True).order_by(Office.name).all()
    return jsonify([
        {
            'id': o.id,
            'name': o.name,
            'slug': o.slug,
            'description': o.description or '',
            'max_capacity': o.max_queue_capacity,
            'active_counters': o.active_counters,
            'open_time': o.office_open_time.strftime('%H:%M') if o.office_open_time else None,
            'close_time': o.office_close_time.strftime('%H:%M') if o.office_close_time else None,
        }
        for o in offices
    ]), 200


@api_bp.route('/queue/join', methods=['POST'])
def api_join_queue():
    """Join a queue. Accepts JSON body."""
    data = request.get_json(silent=True) or {}

    required = ['office_id', 'matric_no', 'full_name', 'department', 'category_id', 'description']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400

    student_data = {
        'matric_no': data['matric_no'].strip().upper(),
        'full_name': data['full_name'].strip(),
        'department': data['department'].strip(),
        'phone_number': data.get('phone_number', '').strip() or None,
    }
    complaint_data = {
        'category_id': int(data['category_id']),
        'description': data['description'].strip(),
    }

    token, error = join_queue(int(data['office_id']), student_data, complaint_data)

    if error:
        return jsonify({'error': error}), 422

    return jsonify({
        'token_id': token.id,
        'token_number': token.token_number,
        'status': token.status,
        'message': f'You have joined the queue. Your token is #{token.token_number:03d}',
    }), 201


@api_bp.route('/queue/status/<int:token_id>', methods=['GET'])
def api_queue_status(token_id):
    """Get status for a specific token."""
    data = get_queue_status(token_id)
    if not data:
        return jsonify({'error': 'Token not found.'}), 404
    return jsonify(data), 200


@api_bp.route('/queue/cancel/<int:token_id>', methods=['POST'])
def api_cancel_token(token_id):
    """Cancel a token."""
    success, error = cancel_token(token_id)
    if error:
        return jsonify({'error': error}), 422
    return jsonify({'message': 'Token cancelled successfully.'}), 200


# ------------------------------------------------------------------
# Staff endpoints (require login)
# ------------------------------------------------------------------

@api_bp.route('/staff/waitlist', methods=['GET'])
@login_required
@role_required('staff')
def api_waitlist():
    """Return the waitlist for the logged-in staff's office."""
    from datetime import date
    waitlist = get_waitlist(current_user.office_id)
    
    current_serving = QueueToken.query.filter_by(
        office_id=current_user.office_id,
        queue_date=date.today(),
        assigned_staff_id=current_user.id,
        status='being_served'
    ).first()
    
    my_served = QueueToken.query.filter_by(
        office_id=current_user.office_id,
        queue_date=date.today(),
        assigned_staff_id=current_user.id,
        status='completed'
    ).count()
    
    my_skipped = QueueToken.query.filter_by(
        office_id=current_user.office_id,
        queue_date=date.today(),
        assigned_staff_id=current_user.id,
        status='skipped'
    ).count()
    
    return jsonify({
        'office': current_user.office.name if current_user.office else '',
        'waitlist': [
            {
                'id': token.id,
                'token_number': token.token_number,
                'student_name': token.student.full_name if token.student else '',
                'student_matric': token.student.matric_no if token.student else '',
                'student_dept': token.student.department if token.student else '',
                'complaint_category': token.complaint.category.name if token.complaint and token.complaint.category else '',
                'complaint_desc': token.complaint.description if token.complaint else '',
                'joined_at': token.joined_at.isoformat() if token.joined_at else None,
            }
            for token in waitlist
        ],
        'my_served_today': my_served,
        'my_skipped_today': my_skipped,
        'currently_serving': {
            'id': current_serving.id,
            'token_number': current_serving.token_number,
            'student_name': current_serving.student.full_name if current_serving.student else '',
            'student_matric': current_serving.student.matric_no if current_serving.student else '',
            'student_dept': current_serving.student.department if current_serving.student else '',
            'complaint_category': current_serving.complaint.category.name if current_serving.complaint and current_serving.complaint.category else '',
            'complaint_desc': current_serving.complaint.description if current_serving.complaint else '',
        } if current_serving else None
    }), 200


@api_bp.route('/staff/call-next', methods=['POST'])
@login_required
@role_required('staff')
def api_call_next():
    """Call the next student in queue."""
    token, error = call_next(current_user)
    if error:
        return jsonify({'error': error}), 422
    return jsonify({
        'token_id': token.id,
        'token_number': token.token_number,
        'status': token.status,
        'student_name': token.student.full_name if token.student else '',
        'message': f'Now serving #{token.token_number:03d}',
    }), 200


@api_bp.route('/staff/complete/<int:token_id>', methods=['POST'])
@login_required
@role_required('staff')
def api_complete(token_id):
    """Mark a token as completed."""
    token = db.session.get(QueueToken, token_id)
    if not token:
        return jsonify({'error': 'Token not found.'}), 404
    if token.office_id != current_user.office_id:
        return jsonify({'error': 'You cannot modify tokens from another office.'}), 403

    token, error = complete_service(token_id, current_user)
    if error:
        return jsonify({'error': error}), 422
    return jsonify({
        'token_id': token.id,
        'token_number': token.token_number,
        'status': token.status,
        'message': f'Token #{token.token_number:03d} completed.',
    }), 200


@api_bp.route('/staff/skip/<int:token_id>', methods=['POST'])
@login_required
@role_required('staff')
def api_skip(token_id):
    """Skip a token."""
    token = db.session.get(QueueToken, token_id)
    if not token:
        return jsonify({'error': 'Token not found.'}), 404
    if token.office_id != current_user.office_id:
        return jsonify({'error': 'You cannot modify tokens from another office.'}), 403

    token, error = skip_token(token_id, current_user)
    if error:
        return jsonify({'error': error}), 422
    return jsonify({
        'token_id': token.id,
        'token_number': token.token_number,
        'status': token.status,
        'message': f'Token #{token.token_number:03d} skipped.',
    }), 200


# ------------------------------------------------------------------
# Office Admin analytics
# ------------------------------------------------------------------

@api_bp.route('/office-admin/analytics', methods=['GET'])
@login_required
@role_required('office_admin')
def api_office_analytics():
    """Return analytics for the logged-in admin's office."""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    data = office_summary(current_user.office_id, date_from, date_to)
    return jsonify(data), 200


# ------------------------------------------------------------------
# Super Admin analytics
# ------------------------------------------------------------------

@api_bp.route('/super-admin/analytics', methods=['GET'])
@login_required
@role_required('super_admin')
def api_university_analytics():
    """Return university-wide analytics."""
    data = university_summary()
    return jsonify(data), 200
