
from app.models import Order, Log, User
from app import db
from uuid import uuid4
import json
from datetime import datetime, timedelta
import pytz
timezone = "Europe/Berlin"

today = datetime.now(tz=pytz.timezone(timezone)).date()

orders = db.session.query(Order).filter(Order.isCancelled == True).order_by(Order.settleTime.desc()).all()

order = orders[0]

db.session.delete(order)

db.session.commit()
