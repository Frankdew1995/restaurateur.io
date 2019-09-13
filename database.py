
from app.models import Order, Log, User
from app import db
from uuid import uuid4
import json
from datetime import datetime, timedelta
import pytz
timezone = "Europe/Berlin"

today = datetime.now(tz=pytz.timezone(timezone)).date()

orders = db.session.query(Order).filter(
    Order.type == "Out").all()


logs = db.session.query(Log).all()

for log in logs:

    db.session.delete(log)
    db.session.commit()
