from flask import Flask, render_template, url_for, request, flash, redirect
from flasktest.forms import RegistrationForm, LoginForm
from flasktest.models import User, Post
from flasktest.database import database
from flasktest import app, db
from flasktest import bcrypt
from flask_login import login_user, login_required, current_user, logout_user


posts = [
    {
        "author": "Ramil Salayev",
        "title": "Post 1",
        "content": "First post",
        "date_posted": "2024-03-03",
    },
    {
        "author": "Ramil Salayev",
        "title": "Post 2",
        "content": "Second post",
        "date_posted": "2024-03-03",
    },
]


@app.route("/")
@app.route("/home")
@login_required
def index():
    return render_template("home.html", posts=posts)


@app.route("/login", methods=["GET", "POST"])
def login():
    print(current_user)
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data

        # database.connect()
        # query = """SELECT * FROM examsystem.users"""
        # result = database.execute(query)
        # database.disconnect()

        user = User.query.filter_by(email=form.email.data).first()

        if user and bcrypt.check_password_hash(user.password, password):
            flash(f"You have been logged in!", category="success")
            login_user(user, remember=form.remember.data)
            return redirect(url_for("index"))
        else:
            flash(
                f"Login Unsuccessful. Please check email and password",
                category="danger",
            )

    return render_template("login2.html", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
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
def about():
    return render_template("about.html", title="About")
