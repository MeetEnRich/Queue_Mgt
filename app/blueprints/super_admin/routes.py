from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required

from app.blueprints.super_admin import super_admin_bp
from app.extensions import db
from app.models import Office
from app.services.analytics_service import office_summary, university_summary
from app.utils.decorators import role_required


# ------------------------------------------------------------------
# Overview
# ------------------------------------------------------------------

@super_admin_bp.route('/overview')
@login_required
@role_required('super_admin')
def overview():
    """University-wide queue dashboard."""
    summary = university_summary()
    return render_template('super_admin/overview.html', summary=summary)


# ------------------------------------------------------------------
# Office Management
# ------------------------------------------------------------------

@super_admin_bp.route('/offices', methods=['GET', 'POST'])
@login_required
@role_required('super_admin')
def offices():
    """List all offices and create new ones."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip().lower()
        description = request.form.get('description', '').strip()
        max_capacity = request.form.get('max_capacity', type=int) or 50
        active_counters = request.form.get('active_counters', type=int) or 1

        if not all([name, slug]):
            flash('Office name and slug are required.', 'error')
        elif Office.query.filter_by(slug=slug).first():
            flash('An office with this slug already exists.', 'error')
        else:
            from datetime import time
            open_time_str = request.form.get('open_time', '08:00').strip()
            close_time_str = request.form.get('close_time', '16:00').strip()

            try:
                from datetime import datetime
                open_t = datetime.strptime(open_time_str, '%H:%M').time()
                close_t = datetime.strptime(close_time_str, '%H:%M').time()
            except ValueError:
                open_t = time(8, 0)
                close_t = time(16, 0)

            office = Office(
                name=name,
                slug=slug,
                description=description,
                max_capacity=max_capacity,
                active_counters=active_counters,
                open_time=open_t,
                close_time=close_t,
                is_active=True,
            )
            db.session.add(office)
            db.session.commit()
            flash(f'Office "{name}" created successfully.', 'success')
            return redirect(url_for('super_admin.offices'))

    all_offices = Office.query.order_by(Office.name).all()
    return render_template('super_admin/offices.html', offices=all_offices)


@super_admin_bp.route('/offices/<office_slug>/toggle', methods=['POST'])
@login_required
@role_required('super_admin')
def toggle_office(office_slug):
    """Activate or deactivate an office."""
    office = Office.query.filter_by(slug=office_slug).first_or_404()
    office.is_active = not office.is_active
    db.session.commit()

    status = 'activated' if office.is_active else 'deactivated'
    flash(f'Office "{office.name}" has been {status}.', 'success')
    return redirect(url_for('super_admin.offices'))


@super_admin_bp.route('/offices/<office_slug>')
@login_required
@role_required('super_admin')
def office_detail(office_slug):
    """Drill into one office's analytics (read-only)."""
    office = Office.query.filter_by(slug=office_slug).first_or_404()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    summary = office_summary(office.id, date_from, date_to)

    return render_template(
        'super_admin/overview.html',
        summary={'offices': [summary]},
        drill_office=office,
    )
