from datetime import datetime
from flasktest import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    image = db.Column(db.String(20), nullable=False, default="default.jpg")
    faculty_id = db.Column(db.Integer, nullable=True, default=None)
    is_superuser = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self) -> str:
        return f"User: {self.username}"
