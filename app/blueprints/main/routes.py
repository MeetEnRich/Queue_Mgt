from flask import render_template

from app.blueprints.main import main_bp
from app.models import Office


@main_bp.route('/')
def office_directory():
    """Public landing page — lists every active office."""
    offices = Office.query.filter_by(is_active=True).order_by(Office.name).all()
    return render_template('main/office_directory.html', offices=offices)
