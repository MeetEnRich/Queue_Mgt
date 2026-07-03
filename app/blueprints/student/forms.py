from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Regexp


class RegisterForm(FlaskForm):
    """Student queue registration form."""
    matric_no = StringField(
        'Matric Number',
        validators=[
            DataRequired(message='Matric number is required.'),
            Regexp(
                r'^\d{4}/[A-Z]{2,4}/[A-Z]{2,5}/\d{4}$',
                message='Format: YYYY/FACULTY/DEPT/NNNN (e.g. 2021/CP/CSC/0295)'
            )
        ],
        render_kw={'placeholder': 'e.g. 2021/CP/CSC/0295'}
    )
    full_name = StringField(
        'Full Name',
        validators=[DataRequired(message='Full name is required.')],
        render_kw={'placeholder': 'Enter your full name'}
    )
    department = StringField(
        'Department',
        validators=[DataRequired(message='Department is required.')],
        render_kw={'placeholder': 'e.g. Computer Science'}
    )
    phone_number = StringField(
        'Phone Number',
        validators=[Optional()],
        render_kw={'placeholder': 'e.g. 08012345678 (optional)'}
    )
    category_id = SelectField(
        'Complaint Category',
        coerce=int,
        validators=[DataRequired(message='Please select a category.')]
    )
    description = TextAreaField(
        'Description',
        validators=[DataRequired(message='Please describe your complaint/request.')],
        render_kw={
            'placeholder': 'Briefly describe your complaint or request...',
            'rows': 4
        }
    )
    submit = SubmitField('Join Queue')
