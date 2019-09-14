from flask import (Flask, render_template,
                   url_for, redirect, flash,
                   request, jsonify, make_response,
                   send_file)

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin
from flask_caching import Cache

from config import Config

app = Flask(__name__)

# Configure from a Python object
app.config.from_object(Config)

db = SQLAlchemy(app)

migrate = Migrate(app, db)

login = LoginManager(app)

cache = Cache(app)

# Set the Login View to protect a view
login.login_view = "login"

from app import routes, models







