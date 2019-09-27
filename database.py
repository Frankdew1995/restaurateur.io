
from app.models import Order, Log, User, Table
from app import db
from uuid import uuid4
import json
from datetime import datetime, timedelta
import pytz
timezone = "Europe/Berlin"

from app.models import Food

today = datetime.now(tz=pytz.timezone(timezone)).date()

orders = db.session.query(Order).all()


for order in orders:

    if not order.isCancelled:

        db.session.delete(order)
        db.session.commit()