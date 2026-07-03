from flask import render_template
from flask_login import current_user, login_required

from app.blueprints.staff import staff_bp
from app.services.queue_service import get_waitlist
from app.utils.decorators import role_required


@staff_bp.route('/dashboard')
@login_required
@role_required('staff')
def dashboard():
    """Staff dashboard — shows current queue and action buttons."""
    office = current_user.office
    waitlist = get_waitlist(current_user.office_id)

    return render_template(
        'staff/dashboard.html',
        office=office,
        waitlist=waitlist,
    )
