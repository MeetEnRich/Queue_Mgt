from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.blueprints.auth import auth_bp
from app.blueprints.auth.forms import LoginForm
from app.models import Staff


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Staff / Admin login page."""
    if current_user.is_authenticated:
        return _redirect_by_role(current_user.role)

    form = LoginForm()

    if form.validate_on_submit():
        staff = Staff.query.filter_by(username=form.username.data.strip()).first()

        if staff and staff.check_password(form.password.data):
            if not staff.is_active:
                flash('Your account has been deactivated. Contact an administrator.', 'error')
                return render_template('auth/login.html', form=form)

            login_user(staff, remember=True)
            flash(f'Welcome back, {staff.full_name}!', 'success')

            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return _redirect_by_role(staff.role)
        else:
            flash('Invalid username or password.', 'error')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _redirect_by_role(role: str):
    """Redirect a logged-in user to the appropriate dashboard."""
    destinations = {
        'super_admin': 'super_admin.overview',
        'office_admin': 'office_admin.dashboard',
        'staff': 'staff.dashboard',
    }
    return redirect(url_for(destinations.get(role, 'main.office_directory')))
