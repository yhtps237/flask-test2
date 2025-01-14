from collections import defaultdict
import datetime
from flask import (
    Flask,
    abort,
    render_template,
    url_for,
    request,
    flash,
    redirect,
    jsonify,
)

import json
from flasktest.forms import (
    RegistrationForm,
    LoginForm,
    StudentPhoneNumber,
    UpdateAccountForm,
    ContingentForm,
    StudentsForm,
    DeleteTopicForm,
)
from flasktest.models import User
from flasktest.database import database, connect_db, disconnect_db, load_config
from flasktest import app, db
from flasktest import bcrypt
from flask_login import login_user, login_required, current_user, logout_user
from PIL import Image
from flask import send_file
import requests
import secrets
import os
import io
import asyncio
from flasktest.modules.module import Contingent, Ejurnal, MovementReport, Students
import pandas as pd
from .helpers import check_whatsapp_exists, send_message

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
def get_professions():
    faculty_id = request.args.get("faculty_name", type=int)
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


@app.route("/ejurnal", methods=["GET", "POST"])
@login_required
async def ejurnal_view():
    # ---------------------------------------------------------
    form = ContingentForm()
    faculty_names = await database.get_faculty_names()
    form.faculty_name.choices = faculty_names
    # ---------------------------------------------------------
    # current_year = datetime.datetime.now().year

    if request.method == "POST":
        if form.validate_on_submit():
            faculty_id = form.faculty_name.data
            start_date = form.start_date.data
            end_date = form.end_date.data
            ejurnal = Ejurnal(faculty_id, start_date, end_date)

            await ejurnal.initialize()

            ejurnal.save(f"{faculty_id}-students")

            return send_file(
                f"../excel-files/{faculty_id}-students.xlsx",
                as_attachment=True,
                download_name=f"{faculty_id}-students.xlsx",
                mimetype="application/excel",
            )
            return redirect(request.url)
        else:
            print(form.errors)

    return render_template(
        "ejurnal.html", title="Ejurnal", form=form, faculty_names=faculty_names
    )


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
# @login_required
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
    return render_template("student_number2.html", title="Tələbə", form=form)


@app.route("/delete-movement/<int:pk>", methods=["GET"])
@login_required
def delete_movement(pk):
    # current_user.faculty_id
    # ---------------------------------------------------------
    connection = connect_db(database)
    with connection.cursor() as cursor:

        query = f"""DELETE from examsystem.contingent_movements
                    where id={pk};
                """
        cursor.execute(query)
        connection.commit()

    disconnect_db(connection, database)
    # ---------------------------------------------------------
    return redirect(url_for("index"))


# =============================================================
@app.route("/empty-topics", methods=["GET"])
@login_required
async def empty_topics():
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
        if current_user.is_superuser:
            query = f"""SELECT id, db_name, profession_name,  course_name, subject_name, 
                        topic_name, topic_id,status, request_user_id, confirm_user_id, 
                        request_text, answer_text, created_at
                        from examsystem.contingent_empty_topics_requests
                    """
        else:
            query = f"""SELECT id, db_name, profession_name,  course_name, subject_name, 
                        topic_name, topic_id,status, request_user_id, confirm_user_id, 
                        request_text, answer_text, created_at
                        from examsystem.contingent_empty_topics_requests
                        WHERE request_user_id={current_user.id}
                    """

        cursor.execute(query)
        results = cursor.fetchall()
        user_ids = [row[8] for row in results]
        users = User.query.filter(User.id.in_(user_ids)).all()
        user_map = {user.id: user for user in users}
        # Sort the list of tuples by the 'db_name' which is at index 7
        # sorted_tuples = sorted(results, key=lambda x: x[7])
        # # print(sorted_tuples)
        # # Convert the sorted list of tuples to a dictionary, using 'db_name' (index 7) as the key
        # sorted_dict = defaultdict(list)
        # for t in sorted_tuples:
        #     sorted_dict[t[7]].append(t)

        # data = {}

        # for db_name, ids in sorted_dict.items():
        #     # print(db_name, ids)
        #     result = await database.get_ejurnal_fields(db_name, ids)
        #     data[db_name] = result

        # Print the resulting dictionary
        # for db_name, topics in data.items():
        #     print(db_name, topics)
        # print(data)

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

    return render_template(
        "requests/empty_topics.html", results=results, user_map=user_map
    )


@app.route("/delete-topic", methods=["GET"])
@login_required
async def remove_topic_delete_request():

    if not current_user.is_superuser:
        raise abort(403, "You do not have permission to access this resource.")

    row_id = request.args.get("pk")

    connection = connect_db(database)
    with connection.cursor() as cursor:

        query = f"""DELETE from examsystem.contingent_empty_topics_requests
                    WHERE id={row_id}
                """

        cursor.execute(query)
        connection.commit()

    disconnect_db(connection, database)
    previous_url = request.referrer  # Get the referrer URL
    if previous_url:
        return redirect(previous_url)
    return redirect("/")


@app.route("/reject-topic", methods=["GET"])
@login_required
async def reject_topic_delete_request():

    if not current_user.is_superuser:
        raise abort(403, "You do not have permission to access this resource.")

    row_id = request.args.get("pk")
    topic_id = request.args.get("topic_id")
    reason = request.args.get("reason")
    db_name = request.args.get("db")

    connection = connect_db(database)
    with connection.cursor() as cursor:

        await database.delete_ejurnal_topic(db_name, topic_id)

        query = f"""UPDATE examsystem.contingent_empty_topics_requests
                    SET status=3, confirm_date=CURRENT_TIMESTAMP,
                    confirm_user_id={current_user.id},
                    answer_text='{reason}'
                    WHERE id={row_id}
                """

        cursor.execute(query)
        connection.commit()

    disconnect_db(connection, database)
    previous_url = request.referrer  # Get the referrer URL
    if previous_url:
        return redirect(previous_url)
    return redirect("/")


@app.route("/confirm-topic", methods=["GET"])
@login_required
async def confirm_topic_delete_request():

    if not current_user.is_superuser:
        raise abort(403, "You do not have permission to access this resource.")

    row_id = request.args.get("pk")
    topic_id = request.args.get("topic_id")
    db_name = request.args.get("db")

    connection = connect_db(database)
    with connection.cursor() as cursor:

        await database.delete_ejurnal_topic(db_name, topic_id)

        query = f"""UPDATE examsystem.contingent_empty_topics_requests
                    SET status=2, confirm_date=CURRENT_TIMESTAMP,
                    confirm_user_id={current_user.id}
                    WHERE id={row_id}
                """

        cursor.execute(query)
        connection.commit()

    disconnect_db(connection, database)
    previous_url = request.referrer  # Get the referrer URL
    if previous_url:
        return redirect(previous_url)
    return redirect("/")


@app.route("/view-topic", methods=["GET"])
@login_required
async def view_topic_delete_request():

    row_id = request.args.get("pk")

    connection = connect_db(database)
    with connection.cursor() as cursor:

        query = f"""SELECT * from examsystem.contingent_empty_topics_requests
                    WHERE id={row_id}
                """

        cursor.execute(query)
        result = cursor.fetchone()
        request_user_id = result[7]
        user_id = result[8]
        user = User.query.get(user_id)
        split_result = result[5].split(" - ")

    disconnect_db(connection, database)
    if not current_user.is_superuser and current_user.id != request_user_id:
        raise abort(403, "You do not have permission to access this resource.")

    return render_template(
        "requests/view_topic_delete_request.html",
        result=result,
        confirm_user=user,
        split_result=split_result,
    )


@app.route("/get_ejurnal_professions")
async def get_ejurnal_professions():
    db_name = request.args.get("faculty_name", type=str)
    profession_names = await database.get_profession_names(db_name)
    profession_names.insert(0, (0, "---"))
    return render_template("professions.html", profession_names=profession_names)


@app.route("/get_ejurnal_courses")
async def get_ejurnal_courses():
    db_name = request.args.get("faculty_name", type=str)
    profession_name = request.args.get("profession_name", type=str)
    # Fetch courses based on db_name and profession_name
    courses = await database.get_course_names(db_name, profession_name)
    # Return the rendered course dropdown
    courses.insert(0, (0, "---"))
    return render_template("courses.html", courses=courses)


@app.route("/get_ejurnal_subjects")
async def get_ejurnal_subjects():
    db_name = request.args.get("faculty_name", type=str)
    course_name = request.args.get("course_name", type=str)
    subject_names = await database.get_subject_names(db_name, course_name)
    subject_names.insert(0, (0, "---"))
    return render_template("subjects.html", subjects=subject_names)


@app.route("/get_ejurnal_topics")
async def get_ejurnal_topics():
    db_name = request.args.get("faculty_name", type=str)
    subject_name = request.args.get("subject_name", type=str)
    topic_names = await database.get_topic_names(db_name, subject_name)
    topic_names.insert(0, (0, "---"))

    return render_template("topics.html", topics=topic_names)


@app.route("/add-topic-delete-request", methods=["GET", "POST"])
@login_required
async def new_topic_to_delete():

    form = DeleteTopicForm()

    faculty_names = await database.get_faculty_names()
    form.faculty_name.choices = faculty_names
    first_faculty_name = faculty_names[0][0]
    if request.method == "POST":
        first_faculty_name = form.faculty_name.data
    profession_names = await database.get_profession_names(first_faculty_name)
    profession_names.insert(0, (0, "---"))
    form.profession_name.choices = profession_names

    if request.method == "POST":
        form.course_name.choices = [(0, "---")] + await database.get_course_names(
            first_faculty_name, form.profession_name.data
        )
        form.subject_name.choices = [(0, "---")] + await database.get_subject_names(
            first_faculty_name, form.course_name.data
        )
        form.topic_name.choices = [(0, "---")] + await database.get_topic_names(
            first_faculty_name, form.subject_name.data
        )
    else:
        form.course_name.choices = [(0, "---")]
        form.subject_name.choices = [(0, "---")]

        form.topic_name.choices = [(0, "---")]

    if request.method == "POST":
        if form.validate_on_submit():
            db_name = form.faculty_name.data
            profession_name = await database.get_profession_name_by_id(
                form.faculty_name.data, form.profession_name.data
            )
            course_name = await database.get_course_name_by_id(
                form.faculty_name.data, form.course_name.data
            )
            subject_name = await database.get_subject_name_by_id(
                form.faculty_name.data, form.subject_name.data
            )
            topic_name = await database.get_topic_name_by_id(
                form.faculty_name.data, form.topic_name.data
            )
            topic_id = form.topic_name.data
            text = form.text.data
            print(db_name)
            print(profession_name)
            print(course_name)
            print(subject_name)
            print(topic_name)
            print(topic_id)
            # ---------------------------------------------------------
            connection = connect_db(database)

            with connection.cursor() as cursor:
                query = f"""INSERT INTO examsystem.contingent_empty_topics_requests(db_name, profession_name, course_name,
                            subject_name, topic_name, topic_id, request_user_id, request_text)
                            VALUES('{db_name}', '{profession_name}', '{course_name}', '{subject_name}',
                            '{topic_name}', {topic_id}, {current_user.id}, '{text}');
                        """
                cursor.execute(query)

                connection.commit()

            disconnect_db(connection, database)

            flash("Form successfully submitted!", "success")
            previous_url = request.referrer  # Get the referrer URL
            if previous_url:
                return redirect(previous_url)
            return redirect("/")
            # return redirect(url_for("new_topic_to_delete"))

    # ---------------------------------------------------------

    if request.method == "POST":
        if form.validate_on_submit():
            # faculty_id = form.faculty_name.data
            # profession_id = form.profession_name.data
            # edu = form.eduyear.data
            # sm = form.semestr.data
            # start_date = form.start_date.data
            # end_date = form.end_date.data
            # radio = form.radio.data
            # contingent = Contingent(
            #     edu, sm, faculty_id, profession_id, start_date, end_date, radio
            # )
            # contingent.save(f"{start_date}-{end_date}-{radio}")

            # return send_file(
            #     f"../excel-files/{start_date}-{end_date}-{radio}.xlsx",
            #     as_attachment=True,
            #     download_name=f"{start_date}-{end_date}-{radio}.xlsx",
            #     mimetype="application/excel",
            # )
            pass
            # return redirect(request.url)
        else:
            print(form.errors)

    # if request.args.get("export") == "True":
    #     report_obj = MovementReport(results, current_user.faculty_id)

    #     report_obj.save("report")
    #     return send_file(
    #         "../excel-files/report.xlsx",
    #         as_attachment=True,
    #         download_name="report.xlsx",
    #         mimetype="application/excel",
    #     )
    return render_template("requests/add_topic_to_delete.html", form=form)


@app.route("/exams", methods=["GET", "POST"])
@login_required
def show_exams():
    if current_user.faculty_id != 0:
        return redirect(url_for("index"))

    if request.method == "POST":
        try:
            # Extract data from the form
            subject_name = request.form.get("subject_name")
            teacher_name = request.form.get("teacher_name")
            phone_number = request.form.get("phone_number")
            date = request.form.get("date")
            if phone_number == "None":
                return (
                    jsonify(
                        {"success": False, "message": "Telefon nömrəsi tapılmadı."}
                    ),
                    500,
                )
            # Log or process the data (replace this with your desired action)
            print(
                f"Subject: {subject_name}, Teacher: {teacher_name}, Phone: {phone_number}, Date: {date}"
            )
            config = load_config()
            waInstance = config["waInstance"]
            apiTokenInstance = config["apiTokenInstance"]
            whatsapp_check = check_whatsapp_exists(
                waInstance, apiTokenInstance, phone_number
            )
            if not whatsapp_check:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Verilmiş nömrə WhatsApp qeydiyyatında deyil.",
                        }
                    ),
                    500,
                )
            msg = f"""Hörmətli {teacher_name}. Sizin {date} tarixdə keçirilmiş "{subject_name}" imtahanınız imtahan vərəqələri yoxlanmaq üçün hazırdır. Yoxlamaq üçün müvafiq təhsil müəssisəsinə dəvət olunursunuz.
                    """
            status = send_message(waInstance, apiTokenInstance, phone_number, msg)
            if status:
                return jsonify({"success": True, "message": "Mesaj uğurla göndərildi!"})
            return jsonify(
                {"success": False, "message": "Mesaj göndərilən zaman xəta baş verdi!"}
            )

        except Exception as e:
            print(f"Error: {str(e)}")
            return (
                jsonify({"success": False, "message": "Mesaj göndərilə bilmədi."}),
                500,
            )

    connection = connect_db(database)

    with connection.cursor() as cursor:
        query = """SELECT db_name, faculty_name from examsystem.faculty_names"""
        cursor.execute(query)
        db_names = cursor.fetchall()
        # db_names = [i[0] for i in db_names]
        query = """"""

        for index, (db_name, faculty_name) in enumerate(db_names):
            temp_query = (
                f"""SELECT '{faculty_name}', profession_name, {db_name}.course, {db_name}.id,  
                    {db_name}.subjectName, {db_name}.teacherName, {db_name}.examType, 
                    {db_name}.subjectClass, {db_name}.isSub, {db_name}.isExamHappend, 
                    {db_name}.startDate, {db_name}.startTime, dpt.department_name, 
                    {db_name}.is_checked, {db_name}.phone_number
                    FROM {db_name}.subjects as {db_name}  
                    JOIN examsystem.professions as pr ON pr.id={db_name}.profession_id 
                    LEFT JOIN examsystem.departments as dpt ON dpt.id={db_name}.department_id 
                    where educationYear='2024/2025' and semestr='PAYIZ' and examType='Yazılı' \n"""
                if index == 0
                else f"""UNION ALL SELECT '{faculty_name}', profession_name, {db_name}.course, {db_name}.id,  
                        {db_name}.subjectName, {db_name}.teacherName, {db_name}.examType, 
                        {db_name}.subjectClass, {db_name}.isSub, {db_name}.isExamHappend, 
                        {db_name}.startDate, {db_name}.startTime, dpt.department_name, 
                        {db_name}.is_checked, {db_name}.phone_number 
                        FROM {db_name}.subjects as {db_name} 
                        JOIN examsystem.professions as pr ON pr.id={db_name}.profession_id 
                        LEFT JOIN examsystem.departments as dpt ON dpt.id={db_name}.department_id 
                        where educationYear='2024/2025' and semestr='PAYIZ' and examType='Yazılı'\n"""
            )
            query += temp_query
        cursor.execute(query)
        results = cursor.fetchall()

    disconnect_db(connection, database)

    if request.args.get("export") == "True":
        # report_obj = MovementReport(results, current_user.faculty_id)

        # report_obj.save("report")
        columns = [
            "Fakültə adı",
            "İxtisas adı",
            "Kurs",
            "ID",
            "Fənn",
            "Müəllim",
            "İmtahan növü",
            "Qrub",
            "Alt/qrup",
            "İmtahan olub",
            "Tarix",
            "Saat",
            "Kafedra adı",
            "Yoxlanılıb",
            "Telefon",
        ]
        dataframe = pd.DataFrame(data=results, columns=columns)
        dataframe.to_excel("excel-files/exams.xlsx", index=False)
        # print(dataframe)
        return send_file(
            "../excel-files/exams.xlsx",
            as_attachment=True,
            download_name="report.xlsx",
            mimetype="application/excel",
        )

    return render_template("exams/exams_view.html", results=results)


@app.route("/edit-phone-number/", methods=["GET", "POST"])
@login_required
def edit_phone_number():
    if current_user.faculty_id != 0:
        return redirect(url_for("index"))

    if request.method == "POST":
        row_id = request.form.get("id")
        db_name = request.form.get("db_name")
        phone = request.form.get("phone")

        if not phone or not id or not db_name:
            return (
                jsonify({"success": False, "message": "All fields are required"}),
                400,
            )

        connection = connect_db(database)
        with connection.cursor() as cursor:

            query = f"""UPDATE {db_name}.subjects SET phone_number='{phone}' where id={row_id}"""
            cursor.execute(query)
            connection.commit()

        disconnect_db(connection, database)
        flash("Uğurla yerinə yetirildi!", "success")
        return redirect(request.referrer)

    row_id = request.args.get("row_id")
    faculty_name = request.args.get("faculty_name")
    connection = connect_db(database)

    with connection.cursor() as cursor:
        query = f"""SELECT db_name from examsystem.faculty_names where faculty_name='{faculty_name}'"""
        cursor.execute(query)
        db_name = cursor.fetchall()[0][0]

        query = f"""SELECT id, subjectName, teacherName, phone_number from {db_name}.subjects where id={row_id}"""
        cursor.execute(query)
        result = cursor.fetchone()

    disconnect_db(connection, database)
    print(result)
    return render_template(
        "exams/edit_phone_number.html", result=result, db_name=db_name
    )


@app.route("/update-status", methods=["POST"])
def update_status():
    try:
        # Get the JSON data from the request
        data = request.get_json()
        record_id = data.get("id")
        faculty_name = data.get("faculty_name")
        status = data.get("status")

        connection = connect_db(database)

        with connection.cursor() as cursor:
            query = f"""SELECT db_name from examsystem.faculty_names where faculty_name='{faculty_name}'"""
            cursor.execute(query)
            db_name = cursor.fetchall()[0][0]
            query = f"""UPDATE {db_name}.subjects SET is_checked={status} where id={record_id}"""
            print(query)
            cursor.execute(query)
            connection.commit()

        disconnect_db(connection, database)

        return jsonify({"message": "Status updated successfully!"})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An error occurred while updating the status."}), 500
