
from app.models import Order
from app import db
from uuid import uuid4
import json
from datetime import datetime
import pytz
timezone = "Europe/Berlin"

today = datetime.now(tz=pytz.timezone(timezone)).date()


paid_orders = db.session.query(Order).filter(
        Order.isPaid == True).order_by(Order.settleTime.desc()).all()

print(paid_orders)

from_time = paid_orders[-1].settleTime

print(from_time)