from app import db, login

from flask_login import UserMixin
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash


class Food(db.Model):

    id = db.Column(db.Integer, primary_key=True, index=True, unique=True)
    name = db.Column(db.String(100), unique=False, nullable=False)
    category = db.Column(db.String(100), unique=False, nullable=False)
    class_name = db.Column(db.String(100))
    description = db.Column(db.String(200), unique=False, nullable=False)
    price_gross = db.Column(db.Float(2), nullable=False)
    price_net_out = db.Column(db.Float(2), nullable=False)
    price_net_in = db.Column(db.Float(2), nullable=False)
    eat_manner = db.Column(db.String(100))
    image = db.Column(db.String(100), nullable=False)
    container = db.Column(db.String(300))

    inUse = db.Column(db.Boolean, default=True)
    cn_description = db.Column(db.String(500))

    def __repr__(self):

        return f"Food: {self.name}"


class Table(db.Model):

    id = db.Column(db.Integer, primary_key=True, unique=True, index=True)
    name = db.Column(db.String(100), unique=True)
    number = db.Column(db.Integer, nullable=False, unique=False)
    section = db.Column(db.String(10), unique=False)
    seats = db.Column(db.String(100))
    is_on = db.Column(db.Boolean, nullable=False, default=False)
    timeCreated = db.Column(db.DateTime, default=datetime.utcnow)
    container = db.Column(db.String(300))

    def __repr__(self):

        return f"Table No.: {self.number}"


@login.user_loader
def load_user(id):

    return User.query.get(int(id))


# Create User Class and inherits from UserMixin
class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    alias = db.Column(db.String(64))
    email = db.Column(db.String(120), unique=True)
    password_hash = db.Column(db.String(128))
    permissions = db.Column(db.Integer)
    container = db.Column(db.String(300))

    def __repr__(self):

        return f'User: {self.username}>'

    def set_password(self, password):

        self.password_hash = generate_password_hash(password=password)

    def check_password(self, password):

        return check_password_hash(self.password_hash, password)


class Order(db.Model):

    id = db.Column(db.Integer, primary_key=True, unique=True, index=True)
    totalPrice = db.Column(db.Float, unique=False)
    orderNumber = db.Column(db.String(200), unique=True)
    timeCreated = db.Column(db.DateTime, default=datetime.utcnow)
    isPaid = db.Column(db.Boolean, default=False)
    isReady = db.Column(db.Boolean, default=False)
    isPickedUp = db.Column(db.Boolean, default=False)
    items = db.Column(db.String(300))
    pay_via = db.Column(db.String(100))
    type = db.Column(db.String(100))
    container = db.Column(db.String(300))
    mealPrinted = db.Column(db.Boolean, default=False)
    printed = db.Column(db.Boolean, default=False)
    settleTime = db.Column(db.DateTime)
    settleID = db.Column(db.String(500))
    table_name = db.Column(db.String(500))
    seat_number = db.Column(db.String(500))
    isCancelled = db.Column(db.Boolean(), default=False)
    dishes = db.Column(db.String(1500))
    discount = db.Column(db.Float)
    discount_rate = db.Column(db.Float)


class Visit(db.Model):

    id = db.Column(db.Integer, primary_key=True, unique=True, index=True)
    count = db.Column(db.Integer, default=0)
    timeVisited = db.Column(db.DateTime, default=datetime.utcnow)


class Log(db.Model):

    id = db.Column(db.Integer, primary_key=True, unique=True, index=True)
    order_id = db.Column(db.Integer, unique=True)
    operation = db.Column(db.String(100))
    page = db.Column(db.String(100))
    desc = db.Column(db.String(2000))
    status = db.Column(db.String(500))
    time = db.Column(db.String(500))


class Holiday(db.Model):

    id = db.Column(db.Integer, primary_key=True, unique=True, index=True)
    name = db.Column(db.String(500))
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)
    timeCreated = db.Column(db.DateTime)
    inUse = db.Column(db.Boolean, default=True)



