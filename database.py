
from app.models import Order, Log
from app import db
from uuid import uuid4
import json
from datetime import datetime, timedelta
import pytz
timezone = "Europe/Berlin"

today = datetime.now(tz=pytz.timezone(timezone)).date()


orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False,
        Order.isCancelled == False).order_by(Order.timeCreated.desc()).all()

order = orders[0]

batches = json.loads(order.dishes)


dt_objs = []

for batch in batches:

    lastOrdered = list(batch.keys())[0]

    dt_obj = datetime.fromtimestamp(float(lastOrdered))

    if batch.get(lastOrdered).get('order_by') == "3" \
            and batch.get(lastOrdered).get('subtype') == "jpbuffet":

        dt_objs.append(dt_obj)


last = max(dt_objs)

next_round_time = last + timedelta(minutes=15)

print(str(next_round_time))