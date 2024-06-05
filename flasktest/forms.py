from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    StringField,
    IntegerField,
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
    password = StringField("Password", validators=[DataRequired()])
    image = FileField("Profil Şəkli", validators=[FileAllowed(["jpg", "png"])])
    submit = SubmitField("Yenilə")

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop("user_id", None)
        super(UpdateAccountForm, self).__init__(*args, **kwargs)

    def validate_username(self, username):
        if current_user.username != username.data:
            user = User.query.filter_by(username=username.data).first()
            if user and user.id != self.user_id:
                raise ValidationError("Bu istifadəçi adı hal-hazırda istifadə olunur.")

    def validate_email(self, email):
        if current_user.email != email.data:
            user = User.query.filter_by(email=email.data).first()
            if user and user.id != self.user_id:
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


class StudentPhoneNumber(FlaskForm):
    faculty_name = SelectField("Fakültə Adı", validators=[DataRequired()])
    profession_name = SelectField("İxtisas Adı", coerce=int)
    course_name = SelectField("Kurs", coerce=int)
    student_name = SelectField("Tələbə adı", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])

    phone_number = StringField(
        "Telefon nömrəsi",
        validators=[
            DataRequired(),
        ],
        description="Telefon nömrəsin bu formada daxil edin: 994-xx-xxx-xx-xx",
    )

    submit = SubmitField("Yaddaşa ver")

    def validate_profession_name(self, profession_name):
        print(type(profession_name.data), profession_name.data)
        if profession_name.data == 0:
            raise ValidationError("Zəhmət olmasa ixtisası seçin.")

    def validate_course_name(self, course_name):
        print(type(course_name.data), course_name.data)
        if course_name.data == 0:
            raise ValidationError("Zəhmət olmasa kursu seçin.")

    def validate_student_name(self, student_name):
        print(type(student_name.data), student_name.data)
        if student_name.data == 0:
            raise ValidationError("Zəhmət olmasa tələbə adınızı seçin.")

    def validate_phone_number(self, phone_number: str):

        if not phone_number.data.startswith("994"):
            raise ValidationError("Zəhmət olmasa nömrənin əvvəlini 994 ilə yazın.")

        if not phone_number.data.count("-") == 4:
            raise ValidationError("Zəhmət olmasa nömrəni düzgün yazın.")

        if len(phone_number.data) > 16:
            raise ValidationError("Zəhmət olmasa nömrəni düzgün yazın.")

        parts = phone_number.data.split("-")

        if not len(parts[1]) == 2:
            raise ValidationError("Zəhmət olmasa nömrəni düzgün yazın.")

        if not len(parts[2]) == 3:
            raise ValidationError("Zəhmət olmasa nömrəni düzgün yazın.")
        if not len(parts[3]) == 2:
            raise ValidationError("Zəhmət olmasa nömrəni düzgün yazın.")
        if not len(parts[4]) == 2:
            raise ValidationError("Zəhmət olmasa nömrəni düzgün yazın.")

        # if current_user.email != email.data:
        #     user = User.query.filter_by(email=email.data).first()
        #     if user and user.id != self.user_id:
        #         raise ValidationError("Bu mail ünvanı hal-hazırda istifadə olunur.")


class StudentsForm(FlaskForm):
    faculty_name = SelectField("Fakültə Adı", validators=[DataRequired()])
    eduyear = SelectField("Tədris ili", validators=[DataRequired()])
    semestr = SelectField("Semestr", validators=[DataRequired()])

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
