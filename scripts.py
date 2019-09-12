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

if len(orders) > 0:

    order = orders[0]

    batches = json.loads(order.dishes)

    dt_objs = []

    for batch in batches:

        last_ordered = list(batch.keys())[0]

        dt_obj = datetime.fromtimestamp(float(last_ordered))

        if batch.get(last_ordered).get('order_by') == seat_number \
                and batch.get(last_ordered).get('subtype') == "jpbuffet":
            dt_objs.append(dt_obj)

    if len(dt_objs) > 0:

        last_ordered = max(dt_objs)

        next_round_time = last_ordered + timedelta(minutes=15)

        now = datetime.now()

        timedelta = next_round_time.minute - now.minute
        print(timedelta)

