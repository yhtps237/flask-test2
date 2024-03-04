from flask import Flask
from flask_login import LoginManager, logout_user
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt


app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
app.config["SECRET_KEY"] = (
    "e8c05ea5780bf5343045e239438c30a3a5498dbbba3d32abf008c6517aff4617"
)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from flasktest import route
