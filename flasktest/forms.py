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
        "İstifadəçi adı", validators=[DataRequired(), Length(min=2, max=20)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Şifrə", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Şifrənin təkrarı", validators=[DataRequired(), EqualTo("password")]
    )
    faculty_name = SelectField("Fakültə Adı")
    submit = SubmitField("Qeydiyatdan keç")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Bu istifadəçi adı hal-hazırda istifadə olunur.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Bu mail ünvanı hal-hazırda istifadə olunur.")


class UpdateAccountForm(FlaskForm):
    username = StringField(
        "İstifadəçi adı", validators=[DataRequired(), Length(min=2, max=20)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    image = FileField("Profil Şəkli", validators=[FileAllowed(["jpg", "png"])])
    submit = SubmitField("Yenilə")

    def validate_username(self, username):
        if current_user.username != username.data:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError("Bu istifadəçi adı hal-hazırda istifadə olunur.")

    def validate_email(self, email):
        if current_user.email != email.data:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError("Bu mail ünvanı hal-hazırda istifadə olunur.")


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

    submit = SubmitField("Çap et")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Şifrə", validators=[DataRequired()])
    remember = BooleanField("Məni xatırla")
    submit = SubmitField("Daxil ol")
