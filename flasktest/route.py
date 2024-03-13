import datetime
from flask import Flask, render_template, url_for, request, flash, redirect
from flasktest.forms import (
    RegistrationForm,
    LoginForm,
    UpdateAccountForm,
    ContingentForm,
)
from flasktest.models import User, Post
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
from flasktest.modules.module import Contingent


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        commandment_number = request.form["number"]
        r = requests.get(
            f"https://api.ndu.edu.az/download-contingent-file?commandment_number={commandment_number}"
        )
        with open("asdf.pdf", "wb") as f:
            f.write(r.content)

        return send_file(
            io.BytesIO(r.content),
            # as_attachment=True,
            # download_name="image.jpg",
            mimetype="application/pdf",
        )
        # return redirect(url_for("index"))

    connection = connect_db(database)
    with connection.cursor() as cursor:
        query = """SELECT faculty_name, profession_name, course, student_name,
                    ci.category_name, cg.category_name, goners_action, date, commandment_number,
                    pdf_file
                    FROM examsystem.contingent_movements AS cm
                    JOIN examsystem.faculty_names AS fn ON fn.id=cm.faculty_id
                    JOIN examsystem.professions AS pn ON pn.id=cm.profession_id
                    LEFT JOIN examsystem.contingent_incomers AS ci ON ci.id=cm.incomers_action
                    LEFT JOIN examsystem.contingent_goners AS cg ON cg.id=cm.goners_action
                """
        cursor.execute(query)
        results = cursor.fetchall()
    disconnect_db(connection, database)
    return render_template("home.html", results=results)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data

        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password, password):
            flash(f"You have been logged in!", category="success")
            login_user(user, remember=form.remember.data)

            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)

            return redirect(url_for("index"))
        else:
            flash(
                f"Login Unsuccessful. Please check email and password",
                category="danger",
            )

    return render_template("login2.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
@login_required
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash(
            f"Account created for {form.username.data}. Please login.",
            category="success",
        )
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/about")
@login_required
def about():
    return render_template("about.html", title="About")


@app.route("/get_professions")
@login_required
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


@app.route("/contingent", methods=["GET", "POST"])
@login_required
def contingent_vew():
    form = ContingentForm()

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

        query = """SELECT year_name, year_name from examsystem.years;
                """
        cursor.execute(query)
        years = cursor.fetchall()

    disconnect_db(connection, database)
    form.faculty_name.choices = faculty_names
    profession_names.insert(0, (0, "---"))
    print(profession_names)
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
            # return redirect(url_for("index"))
            return redirect(request.url)
        else:
            print(form.errors)
    return render_template("contingent.html", title="contingent", form=form)


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
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.image.data:
            picture_file = save_picture(form.image.data)
            current_user.image = picture_file

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated!", "success")
        return redirect(url_for("account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template(
        "account.html", title=f"Account {username}", image_file=image_file, form=form
    )
