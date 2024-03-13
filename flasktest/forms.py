from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    BooleanField,
    ValidationError,
    SelectField,
    DateField,
    RadioField,
)
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flasktest.models import User
from flask_login import current_user


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Sign up")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("That username is already taken.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("That email is already taken.")


class UpdateAccountForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=20)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    image = FileField("Profile Picture", validators=[FileAllowed(["jpg", "png"])])
    submit = SubmitField("Update")

    def validate_username(self, username):
        if current_user.username != username.data:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError("That username is already taken.")

    def validate_email(self, email):
        if current_user.email != email.data:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError("That email is already taken.")


class ContingentForm(FlaskForm):
    faculty_name = SelectField("Fakültə Adı", validators=[DataRequired()])
    profession_name = SelectField("İxtisas Adı", coerce=int)
    eduyear = SelectField("Tədris ili", validators=[DataRequired()])
    semestr = SelectField("Semestr", validators=[DataRequired()])

    start_date = DateField("Başlama tarixi", validators=[DataRequired()])
    end_date = DateField("Bitmə tarixi", validators=[DataRequired()])
    radio = RadioField(
        "Label",
        choices=[("1", "Əyani"), ("2", "Qiyabi"), ("3", "ƏAT")],
        validators=[DataRequired()],
    )

    submit = SubmitField("Export")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")
