from app.utilities import void_pickle_dumper, formatter

# void_pickle_dumper(r_type="z")
import json
from pathlib import Path
from app import app, db
from app.models import Order
from datetime import datetime, timedelta

seat_number = "1"

orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False,
        Order.isCancelled == False,
        Order.subtype == "jpbuffet",
        Order.table_name == "A1").order_by(Order.timeCreated.desc()).all()

