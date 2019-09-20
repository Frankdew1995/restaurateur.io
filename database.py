
from app.models import Order, Log, User, Table
from app import db
from uuid import uuid4
import json
from datetime import datetime, timedelta
import pytz
timezone = "Europe/Berlin"

today = datetime.now(tz=pytz.timezone(timezone)).date()

orders = db.session.query(Order).order_by(Order.timeCreated.desc()).all()


items = json.loads(orders[0].dishes)

print(items)