from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    """Staff / Admin login form."""
    username = StringField(
        'Username',
        validators=[DataRequired(message='Username is required.')],
        render_kw={'placeholder': 'Enter your username', 'autocomplete': 'username'}
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(message='Password is required.')],
        render_kw={'placeholder': 'Enter your password', 'autocomplete': 'current-password'}
    )
    submit = SubmitField('Login')
