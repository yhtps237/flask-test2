import datetime
from flask import Flask, abort, render_template, url_for, request, flash, redirect
from flasktest.forms import (
    RegistrationForm,
    LoginForm,
    StudentPhoneNumber,
    UpdateAccountForm,
    ContingentForm,
    StudentsForm,
)
from flasktest.models import User
from flasktest.database import database, connect_db, disconnect_db
from flasktest import app, db
from flasktest import bcrypt
from flask_login import login_user, login_required, current_user, logout_user
from PIL import Image
from flask import send_file
import requests
import secrets
import os
import io
from flasktest.modules.module import Contingent, MovementReport, Students

# from flask_bcrypt import generate_password_hash


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        contingent_id = request.form["number"]
        r = requests.get(
            f"https://api.ndu.edu.az/download-contingent-file?commandment_id={contingent_id}"
        )

        return send_file(
            io.BytesIO(r.content),
            mimetype="application/pdf",
        )

    connection = connect_db(database)
    with connection.cursor() as cursor:
        query = """SELECT faculty_name, profession_name, course, student_name,
                    ci.category_name, cg.category_name, date, commandment_number,
                    pdf_file, cm.id, cm.faculty_id
                    FROM examsystem.contingent_movements AS cm
                    JOIN examsystem.faculty_names AS fn ON fn.id=cm.faculty_id
                    JOIN examsystem.professions AS pn ON pn.id=cm.profession_id
                    LEFT JOIN examsystem.contingent_incomers AS ci ON ci.id=cm.incomers_action
                    LEFT JOIN examsystem.contingent_goners AS cg ON cg.id=cm.goners_action
                """
        cursor.execute(query)
        results = cursor.fetchall()
    disconnect_db(connection, database)

    if request.args.get("export") == "True":
        report_obj = MovementReport(results, current_user.faculty_id)

        report_obj.save("report")
        return send_file(
            "../excel-files/report.xlsx",
            as_attachment=True,
            download_name="report.xlsx",
            mimetype="application/excel",
        )

    return render_template("home.html", results=results)


@app.route("/users", methods=["GET", "POST"])
@login_required
def users():
    # if request.method == "POST":
    #     contingent_id = request.form["number"]
    #     r = requests.get(
    #         f"https://api.ndu.edu.az/download-contingent-file?commandment_id={contingent_id}"
    #     )

    #     return send_file(
    #         io.BytesIO(r.content),
    #         mimetype="application/pdf",
    #     )

    connection = connect_db(database)
    with connection.cursor() as cursor:
        query = """SELECT id, faculty_name from examsystem.faculty_names;
                    """
        cursor.execute(query)
        faculty_names = cursor.fetchall()
        faculty_names = dict(faculty_names)
    disconnect_db(connection, database)

    # if request.args.get("export") == "True":
    #     report_obj = MovementReport(results, current_user.faculty_id)

    #     report_obj.save("report")
    #     return send_file(
    #         "../excel-files/report.xlsx",
    #         as_attachment=True,
    #         download_name="report.xlsx",
    #         mimetype="application/excel",
    #     )

    users = User.query.all()
    return render_template("users.html", users=users, faculty_names=faculty_names)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data

        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password, password):
            flash(f"Uğurla giriş edildi!", category="success")
            login_user(user, remember=form.remember.data)

            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)

            return redirect(url_for("index"))
        else:
            flash(
                f"Giriş edilə bilmədi, mail və şifrənizi yoxlayın",
                category="danger",
            )

    return render_template("login2.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/delete-user/<int:pk>")
@login_required
def delete_user(pk):
    if current_user.faculty_id != 0:
        return redirect(url_for("index"))
    if not current_user.is_superuser:
        return redirect(url_for("index"))

    user = User.query.get(pk)
    if not user:
        abort(404)  # Or handle the case where user is not found
    # Delete the user or perform any necessary operations here
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("users"))


@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    if current_user.faculty_id != 0:
        return redirect(url_for("index"))
    if not current_user.is_superuser:
        return redirect(url_for("index"))
    form = RegistrationForm()

    connection = connect_db(database)
    with connection.cursor() as cursor:
        query = """SELECT id, faculty_name from examsystem.faculty_names;
                """
        cursor.execute(query)
        faculty_names = cursor.fetchall()
        faculty_names.insert(0, (0, "---"))

    disconnect_db(connection, database)
    form.faculty_name.choices = faculty_names

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        faculty_id = form.faculty_name.data
        user = User(
            username=username,
            email=email,
            password=hashed_password,
            faculty_id=faculty_id,
        )
        db.session.add(user)
        db.session.commit()

        flash(
            f"Hesab {form.username.data} yaradıldı.",
            category="success",
        )
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/about")
@login_required
def about():
    return render_template("about.html", title="Haqqında")


@app.route("/get_professions")
# @login_required
def get_professions():
    faculty_id = request.args.get("faculty_name", type=int)
    print("faculty_id", faculty_id)
    connection = connect_db(database)
    with connection.cursor() as cursor:
        query = f"""
                    SELECT 
                        pr.id, concat(pr.profession_name, " | ", sector_name)
                    FROM 
                        examsystem.professions as pr
                    JOIN
                        examsystem.sectors as s
                    ON
                        s.id=pr.sectors
                    WHERE 
                        faculty_id={faculty_id};
                """
        cursor.execute(query)
        profession_names = cursor.fetchall()

        profession_names.insert(0, (0, "---"))
    disconnect_db(connection, database)
    return render_template("professions.html", profession_names=profession_names)


@app.route("/get_students")
# @login_required
def get_students():
    faculty_id = request.args.get("faculty_name", type=int)
    profession_id = request.args.get("profession_name", type=int)
    course_name = request.args.get("course_name", type=int)
    connection = connect_db(database)
    with connection.cursor() as cursor:
        query = f"""
                    SELECT 
                        db_name
                    FROM examsystem.faculty_names
                    WHERE 
                        id={faculty_id};
                """
        cursor.execute(query)
        db_name = cursor.fetchall()[0][0]
        query = f"""
                    SELECT education_year, semestr FROM examsystem.options;
                """
        cursor.execute(query)
        result = cursor.fetchall()
        year = result[0][0]
        semestr = result[0][1]

        query = f"""
                    SELECT 
                        id, student_name
                    FROM {db_name}.students
                    WHERE 
                        profession_id={profession_id}
                        AND course={course_name}
                        AND educationYear='{year}'
                        AND semestr='{semestr}'
                        ;
                """
        cursor.execute(query)
        students = cursor.fetchall()

    disconnect_db(connection, database)
    return render_template("student_names.html", students=students)


@app.route("/contingent", methods=["GET", "POST"])
@login_required
def contingent_view():
    form = ContingentForm()

    # ---------------------------------------------------------
    connection = connect_db(database)
    faculty_id = 2
    if request.method == "POST":
        faculty_id = form.faculty_name.data

    with connection.cursor() as cursor:
        if current_user.faculty_id == 0:
            query = """SELECT id, faculty_name from examsystem.faculty_names;
                    """
            cursor.execute(query)
            faculty_names = cursor.fetchall()
        else:
            faculty_id = current_user.faculty_id
            query = f"""SELECT id, faculty_name from examsystem.faculty_names
                        where id={faculty_id};
                    """
            cursor.execute(query)
            faculty_names = cursor.fetchall()

        query = f"""
                    SELECT 
                        pr.id, concat(pr.profession_name, " | ", sector_name)
                    FROM 
                        examsystem.professions as pr
                    JOIN
                        examsystem.sectors as s
                    ON
                        s.id=pr.sectors
                    WHERE 
                        faculty_id={faculty_id}
                """
        cursor.execute(query)
        profession_names = cursor.fetchall()

        query = """SELECT year_name, year_name from examsystem.years;
                """
        cursor.execute(query)
        years = cursor.fetchall()

    disconnect_db(connection, database)
    form.faculty_name.choices = faculty_names
    profession_names.insert(0, (0, "---"))
    form.profession_name.choices = profession_names

    form.eduyear.choices = years
    form.semestr.choices = [("PAYIZ", "PAYIZ"), ("YAZ", "YAZ")]
    # ---------------------------------------------------------
    current_year = datetime.datetime.now().year

    if request.method == "POST":
        if form.validate_on_submit():
            faculty_id = form.faculty_name.data
            profession_id = form.profession_name.data
            edu = form.eduyear.data
            sm = form.semestr.data
            start_date = form.start_date.data
            end_date = form.end_date.data
            radio = form.radio.data
            contingent = Contingent(
                edu, sm, faculty_id, profession_id, start_date, end_date, radio
            )
            contingent.save(f"{start_date}-{end_date}-{radio}")

            return send_file(
                f"../excel-files/{start_date}-{end_date}-{radio}.xlsx",
                as_attachment=True,
                download_name=f"{start_date}-{end_date}-{radio}.xlsx",
                mimetype="application/excel",
            )
            # return redirect(request.url)
        else:
            print(form.errors)
    return render_template("contingent.html", title="Kontingent", form=form)


@app.route("/students", methods=["GET", "POST"])
@login_required
def students_view():
    form = StudentsForm()

    # ---------------------------------------------------------
    connection = connect_db(database)
    faculty_id = 2
    if request.method == "POST":
        faculty_id = form.faculty_name.data

    with connection.cursor() as cursor:
        if current_user.faculty_id == 0:
            query = """SELECT id, faculty_name from examsystem.faculty_names;
                    """
            cursor.execute(query)
            faculty_names = cursor.fetchall()
        else:
            faculty_id = current_user.faculty_id
            query = f"""SELECT id, faculty_name from examsystem.faculty_names
                        where id={faculty_id};
                    """
            cursor.execute(query)
            faculty_names = cursor.fetchall()

        query = """SELECT year_name, year_name from examsystem.years;
                """
        cursor.execute(query)
        years = cursor.fetchall()

    disconnect_db(connection, database)
    form.faculty_name.choices = faculty_names

    form.eduyear.choices = years
    form.semestr.choices = [("PAYIZ", "PAYIZ"), ("YAZ", "YAZ")]
    # ---------------------------------------------------------
    current_year = datetime.datetime.now().year

    if request.method == "POST":
        if form.validate_on_submit():
            faculty_id = form.faculty_name.data
            edu = form.eduyear.data
            sm = form.semestr.data
            radio = form.radio.data
            students = Students(edu, sm, faculty_id, radio)
            students.save(f"{faculty_id}-students-{radio}")

            return send_file(
                f"../excel-files/{faculty_id}-students-{radio}.xlsx",
                as_attachment=True,
                download_name=f"{faculty_id}-students-{radio}.xlsx",
                mimetype="application/excel",
            )
            # return redirect(request.url)
        else:
            print(form.errors)
    return render_template("students.html", title="Tələbələr", form=form)


def save_picture(form_picture):
    hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(form_picture.filename)
    picture_fn = hex + file_ext
    full_path = os.path.join(app.root_path, "static/profile_pics", picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)

    i.save(full_path)

    return picture_fn


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    username = current_user.username
    image_file = url_for("static", filename="profile_pics/" + current_user.image)
    form = UpdateAccountForm(user_id=current_user.id)
    if form.validate_on_submit():
        if form.image.data:
            picture_file = save_picture(form.image.data)
            current_user.image = picture_file

        current_user.username = form.username.data
        current_user.email = form.email.data
        # Check if the user provided a new password
        if form.password.data:
            # Hash the new password
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
                "utf-8"
            )
            current_user.password = hashed_password
        db.session.commit()
        flash("Hesab uğurla yeniləndi!", "success")
        return redirect(url_for("account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.password.data = current_user.password

    return render_template(
        "account.html", title=f"Hesab {username}", image_file=image_file, form=form
    )


@app.route("/edit-account/<int:pk>", methods=["GET", "POST"])
@login_required
def edit_account(pk):
    if current_user.faculty_id != 0:
        return redirect(url_for("index"))
    if not current_user.is_superuser:
        return redirect(url_for("index"))

    user = User.query.get(pk)
    if not user:
        abort(404)

    username = user.username
    image_file = url_for("static", filename="profile_pics/" + user.image)
    form = UpdateAccountForm(user_id=user.id)
    if form.validate_on_submit():
        if form.image.data:
            picture_file = save_picture(form.image.data)
            user.image = picture_file

        user.username = form.username.data
        user.email = form.email.data
        # Check if the user provided a new password
        if form.password.data and form.password.data != user.password:
            # Hash the new password
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
                "utf-8"
            )
            user.password = hashed_password
        db.session.commit()
        flash("Hesab uğurla yeniləndi!", "success")
        return redirect(url_for("edit_account", pk=user.id))
    elif request.method == "GET":
        form.username.data = user.username
        form.email.data = user.email
        form.password.data = user.password

    return render_template(
        "edit_account.html",
        title=f"Hesab {username}",
        image_file=image_file,
        form=form,
        user=user,
    )


@app.route("/student-registration", methods=["GET", "POST"])
def add_student_phone_number():
    form = StudentPhoneNumber()

    # ---------------------------------------------------------
    connection = connect_db(database)
    faculty_id = 2
    if request.method == "POST":
        faculty_id = form.faculty_name.data

    with connection.cursor() as cursor:
        query = """SELECT id, faculty_name from examsystem.faculty_names;
                """
        cursor.execute(query)
        faculty_names = cursor.fetchall()

        query = f"""
                    SELECT 
                        pr.id, concat(pr.profession_name, " | ", sector_name)
                    FROM 
                        examsystem.professions as pr
                    JOIN
                        examsystem.sectors as s
                    ON
                        s.id=pr.sectors
                    WHERE 
                        faculty_id={faculty_id}
                """
        cursor.execute(query)
        profession_names = cursor.fetchall()

        query = f"""
                    SELECT 
                        db_name
                    FROM examsystem.faculty_names
                    WHERE 
                        id={faculty_id};
                """
        cursor.execute(query)
        db_name = cursor.fetchall()[0][0]
        query = f"""
                    SELECT education_year, semestr FROM examsystem.options;
                """
        cursor.execute(query)
        result = cursor.fetchall()
        year = result[0][0]
        semestr = result[0][1]

        query = f"""
                    SELECT 
                        id, student_name
                    FROM {db_name}.students
                    WHERE 
                    educationYear='{year}'
                        AND semestr='{semestr}'
                        ;
                """
        cursor.execute(query)
        students = cursor.fetchall()

    disconnect_db(connection, database)
    form.faculty_name.choices = faculty_names
    profession_names.insert(0, (0, "---"))
    form.profession_name.choices = profession_names

    # form.eduyear.choices = years
    # form.semestr.choices = [("PAYIZ", "PAYIZ"), ("YAZ", "YAZ")]
    form.course_name.choices = [
        (0, "---"),
        ("1", "1"),
        ("2", "2"),
        ("3", "3"),
        ("4", "4"),
        ("5", "5"),
        ("6", "6"),
    ]
    students.insert(0, (0, "---"))

    form.student_name.choices = students

    # ---------------------------------------------------------

    if request.method == "POST":
        if form.validate_on_submit():
            faculty_id = form.faculty_name.data
            profession_id = form.profession_name.data
            course_name = form.course_name.data
            student_name = form.student_name.data
            email = form.email.data
            phone_number = form.phone_number.data
            phone_number = "".join(phone_number.split("-"))
            connection = connect_db(database)
            with connection.cursor() as cursor:
                query = f"""
                            SELECT 
                                db_name
                            FROM examsystem.faculty_names
                            WHERE 
                                id={faculty_id};
                        """
                cursor.execute(query)
                db_name = cursor.fetchall()[0][0]

                query = f"""
                            UPDATE {db_name}.students 
                            SET phone_number='{phone_number}',
                            email='{email}'
                            where id={student_name};
                        """

                # query = f"""
                #             SELECT * FROM {db_name}.students where id={student_name};
                #         """
                cursor.execute(query)
                connection.commit()
            disconnect_db(connection, database)

            flash("Uğurla əlavə edildi.", "success")
            # return redirect(request.url)
            return redirect(request.referrer or url_for("add_student_phone_number"))
        # else:
        #     print(form.errors)
    return render_template("student_number.html", title="Tələbə", form=form)
