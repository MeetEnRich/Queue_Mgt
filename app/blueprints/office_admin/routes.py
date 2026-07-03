import csv
import io
from datetime import datetime, date

from flask import (
    render_template, redirect, url_for, flash, request, Response, send_file
)
from flask_login import current_user, login_required

from app.blueprints.office_admin import office_admin_bp
from app.extensions import db
from app.models import Staff, ComplaintCategory, QueueToken, Office
from app.services.analytics_service import office_summary
from app.services.qr_service import generate_office_qr
from app.utils.decorators import role_required


# ------------------------------------------------------------------
# Dashboard
# ------------------------------------------------------------------

@office_admin_bp.route('/dashboard')
@login_required
@role_required('office_admin')
def dashboard():
    """Office admin analytics dashboard."""
    office = current_user.office
    date_from = request.args.get('date_from', str(date.today()))
    date_to = request.args.get('date_to', str(date.today()))

    summary = office_summary(office.id, date_from, date_to)

    return render_template(
        'office_admin/dashboard.html',
        office=office,
        summary=summary,
        date_from=date_from,
        date_to=date_to,
    )


# ------------------------------------------------------------------
# Staff Management
# ------------------------------------------------------------------

@office_admin_bp.route('/staff', methods=['GET', 'POST'])
@login_required
@role_required('office_admin')
def staff_list():
    """List and create staff for this office."""
    office = current_user.office

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', 'staff')
        counter = request.form.get('counter', type=int)

        if not all([username, password, full_name]):
            flash('All fields are required.', 'error')
        elif Staff.query.filter_by(username=username).first():
            flash('Username already taken.', 'error')
        else:
            new_staff = Staff(
                username=username,
                full_name=full_name,
                role=role if role in ('staff', 'office_admin') else 'staff',
                counter_number=counter,
                office_id=office.id,
                is_active=True,
            )
            new_staff.set_password(password)
            db.session.add(new_staff)
            db.session.commit()
            flash(f'Staff member "{full_name}" created successfully.', 'success')
            return redirect(url_for('office_admin.staff_list'))

    staff_members = Staff.query.filter_by(office_id=office.id).order_by(Staff.full_name).all()

    return render_template(
        'office_admin/staff_list.html',
        office=office,
        staff_members=staff_members,
    )


# ------------------------------------------------------------------
# Complaint Categories
# ------------------------------------------------------------------

@office_admin_bp.route('/categories', methods=['GET', 'POST'])
@login_required
@role_required('office_admin')
def categories():
    """Manage complaint categories for this office."""
    office = current_user.office

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create':
            name = request.form.get('name', '').strip()
            if not name:
                flash('Category name is required.', 'error')
            else:
                cat = ComplaintCategory(name=name, office_id=office.id, is_active=True)
                db.session.add(cat)
                db.session.commit()
                flash(f'Category "{name}" created.', 'success')

        elif action == 'toggle':
            cat_id = request.form.get('category_id', type=int)
            cat = ComplaintCategory.query.filter_by(id=cat_id, office_id=office.id).first()
            if cat:
                cat.is_active = not cat.is_active
                db.session.commit()
                status = 'activated' if cat.is_active else 'deactivated'
                flash(f'Category "{cat.name}" {status}.', 'success')

        return redirect(url_for('office_admin.categories'))

    cats = ComplaintCategory.query.filter_by(office_id=office.id).order_by(ComplaintCategory.name).all()

    return render_template(
        'office_admin/categories.html',
        office=office,
        categories=cats,
    )


# ------------------------------------------------------------------
# Office Settings
# ------------------------------------------------------------------

@office_admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
@role_required('office_admin')
def settings():
    """Office settings — capacity, counters, hours."""
    office = current_user.office

    if request.method == 'POST':
        office.max_capacity = request.form.get('max_capacity', type=int) or office.max_capacity
        office.active_counters = request.form.get('active_counters', type=int) or office.active_counters
        open_time = request.form.get('open_time', '').strip()
        close_time = request.form.get('close_time', '').strip()

        if open_time:
            try:
                office.open_time = datetime.strptime(open_time, '%H:%M').time()
            except ValueError:
                flash('Invalid open time format.', 'error')

        if close_time:
            try:
                office.close_time = datetime.strptime(close_time, '%H:%M').time()
            except ValueError:
                flash('Invalid close time format.', 'error')

        db.session.commit()
        flash('Office settings updated.', 'success')
        return redirect(url_for('office_admin.settings'))

    return render_template(
        'office_admin/settings.html',
        office=office,
    )


# ------------------------------------------------------------------
# CSV Export
# ------------------------------------------------------------------

@office_admin_bp.route('/export')
@login_required
@role_required('office_admin')
def export():
    """Export queue tokens as CSV for a date range."""
    office = current_user.office
    date_from = request.args.get('date_from', str(date.today()))
    date_to = request.args.get('date_to', str(date.today()))

    try:
        dt_from = datetime.strptime(date_from, '%Y-%m-%d')
        dt_to = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    except ValueError:
        dt_from = datetime.combine(date.today(), datetime.min.time())
        dt_to = datetime.combine(date.today(), datetime.max.time())

    tokens = QueueToken.query.filter(
        QueueToken.office_id == office.id,
        QueueToken.created_at >= dt_from,
        QueueToken.created_at <= dt_to,
    ).order_by(QueueToken.created_at).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Token #', 'Student Name', 'Matric No', 'Department',
        'Category', 'Status', 'Joined At', 'Called At',
        'Completed At', 'Served By',
    ])

    for t in tokens:
        writer.writerow([
            t.token_number,
            t.student.full_name if t.student else '',
            t.student.matric_no if t.student else '',
            t.student.department if t.student else '',
            t.complaint.category.name if t.complaint and t.complaint.category else '',
            t.status,
            t.created_at.strftime('%Y-%m-%d %H:%M') if t.created_at else '',
            t.called_at.strftime('%Y-%m-%d %H:%M') if t.called_at else '',
            t.completed_at.strftime('%Y-%m-%d %H:%M') if t.completed_at else '',
            t.served_by_staff.full_name if t.served_by_staff else '',
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={office.slug}_queue_{date_from}_to_{date_to}.csv'
        },
    )


# ------------------------------------------------------------------
# QR Code
# ------------------------------------------------------------------

@office_admin_bp.route('/qr-code')
@login_required
@role_required('office_admin')
def qr_code():
    """Generate and serve the QR code for this office's registration page."""
    office = current_user.office
    img_bytes = generate_office_qr(office)

    return send_file(
        io.BytesIO(img_bytes),
        mimetype='image/png',
        as_attachment=False,
        download_name=f'{office.slug}_qr.png',
    )
