from flask import render_template, redirect, url_for, flash, session, request, abort, current_app

from app.blueprints.student import student_bp
from app.blueprints.student.forms import RegisterForm
from app.models import Office, ComplaintCategory, QueueToken
from app.services.queue_service import join_queue, get_queue_status, cancel_token


@student_bp.route('/<office_slug>/register', methods=['GET', 'POST'])
def register(office_slug):
    """Student queue registration page for a specific office."""
    office = Office.query.filter_by(slug=office_slug).first_or_404()

    if not office.is_active:
        flash('This office is currently not accepting new requests.', 'error')
        return redirect(url_for('main.office_directory'))

    categories = ComplaintCategory.query.filter_by(
        office_id=office.id, is_active=True
    ).order_by(ComplaintCategory.name).all()

    form = RegisterForm()
    form.category_id.choices = [(c.id, c.name) for c in categories]

    if form.validate_on_submit():
        # Geofencing check
        if current_app.config.get('GEOFENCE_ENABLED'):
            lat_str = form.latitude.data
            lng_str = form.longitude.data

            if not lat_str or not lng_str:
                flash('Location access is required to join the queue. Please enable GPS on your device and reload the page.', 'error')
                return render_template(
                    'student/register.html',
                    office=office, categories=categories, form=form,
                )

            try:
                lat = float(lat_str)
                lng = float(lng_str)
            except ValueError:
                flash('Invalid location coordinates received.', 'error')
                return render_template(
                    'student/register.html',
                    office=office, categories=categories, form=form,
                )

            # Haversine Distance Calculation
            import math
            target_lat = current_app.config.get('GEOFENCE_LATITUDE', 8.4746)
            target_lng = current_app.config.get('GEOFENCE_LONGITUDE', 8.5583)
            radius = current_app.config.get('GEOFENCE_RADIUS_METERS', 1500.0)

            dlat = math.radians(target_lat - lat)
            dlon = math.radians(target_lng - lng)
            a = (math.sin(dlat / 2) ** 2 +
                 math.cos(math.radians(lat)) * math.cos(math.radians(target_lat)) * math.sin(dlon / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = 6371000.0 * c  # distance in meters

            if distance > radius:
                flash(f'Registration Denied: You must be physically within the FULafia campus boundaries to join the queue. (Distance: {distance:.0f}m, Limit: {radius:.0f}m)', 'error')
                return render_template(
                    'student/register.html',
                    office=office, categories=categories, form=form,
                )

        student_data = {
            'matric_no': form.matric_no.data.strip().upper(),
            'full_name': form.full_name.data.strip(),
            'department': form.department.data.strip(),
            'phone_number': form.phone_number.data.strip() if form.phone_number.data else None,
        }
        complaint_data = {
            'category_id': form.category_id.data,
            'description': form.description.data.strip(),
        }

        token, error = join_queue(office.id, student_data, complaint_data)

        if error:
            flash(error, 'error')
            return render_template(
                'student/register.html',
                office=office, categories=categories, form=form,
            )

        # Store token in session for tracking
        session['current_token_id'] = token.id
        active_tokens = session.get('active_tokens', [])
        if token.id not in active_tokens:
            active_tokens.append(token.id)
        session['active_tokens'] = active_tokens

        flash(f'You have joined the queue! Your token number is #{token.token_number:03d}', 'success')
        return redirect(url_for('student.status', office_slug=office_slug))

    return render_template(
        'student/register.html',
        office=office, categories=categories, form=form,
    )


@student_bp.route('/<office_slug>/status')
def status(office_slug):
    """Student queue status page — shows position, wait time, etc."""
    office = Office.query.filter_by(slug=office_slug).first_or_404()

    token_id = request.args.get('token_id', type=int) or session.get('current_token_id')

    if not token_id:
        flash('No active queue token found. Please register first.', 'info')
        return redirect(url_for('student.register', office_slug=office_slug))

    token_data = get_queue_status(token_id)

    if not token_data:
        flash('Token not found. It may have expired.', 'error')
        return redirect(url_for('student.register', office_slug=office_slug))

    return render_template(
        'student/status.html',
        office=office, token=token_data,
    )


@student_bp.route('/my-queues')
def my_queues():
    """Show all active tokens tracked in the current session."""
    active_tokens = session.get('active_tokens', [])

    if not active_tokens:
        flash('You have no active queue tickets.', 'info')
        return redirect(url_for('main.office_directory'))

    # If only one active token, redirect straight to its status page
    if len(active_tokens) == 1:
        token = QueueToken.query.get(active_tokens[0])
        if token and token.office:
            return redirect(url_for(
                'student.status',
                office_slug=token.office.slug,
                token_id=token.id,
            ))

    # Multiple tokens — build a list
    tokens = []
    for tid in active_tokens:
        data = get_queue_status(tid)
        if data:
            tokens.append(data)

    return render_template('student/my_queues.html', tokens=tokens)
