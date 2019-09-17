
from app.models import Order, Log, User
from app import db
from uuid import uuid4
import json
from datetime import datetime, timedelta
import pytz
timezone = "Europe/Berlin"

today = datetime.now(tz=pytz.timezone(timezone)).date()


order = db.session.query(Order).get_or_404(321)

dishes = json.loads(order.dishes)

if len(dishes) == 0:

    print({"error": "Leider Ihre Bestellung war "
                    "nicht durchgefuerht. Bitte versuchen Sie erneut."})

else:

    latest_time = str(max([float(list(i.keys())[0]) for i in dishes]))

    print(latest_time)

    latest_order = [i for i in dishes if str(list(i.keys())[0]) == str(latest_time)][0]

    last_batch = latest_order.get(latest_time).get('items')

    details = {'Peking Duck': {'quantity': 3, 'price': 15.0, 'class_name': 'Food', 'order_by': '2'}}

    print(last_batch == details)