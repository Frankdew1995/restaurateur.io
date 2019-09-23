
from app.models import Order, Log, User, Table
from app import db
from uuid import uuid4
import json
from datetime import datetime, timedelta
import pytz
timezone = "Europe/Berlin"

today = datetime.now(tz=pytz.timezone(timezone)).date()

orders = db.session.query(Order).all()

users = db.session.query(User).all()


for user in users:

    user.inUse = True
    db.session.commit()