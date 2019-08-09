from app.models import User, Order, Log
from pathlib import Path

from datetime import datetime

from app import db, app

import json

import pandas as pd

orders = Order.query.all()

for order in orders:

    details = {key: {'qty': items.get('quantity'),
                     'total': items.get('quantity') * items.get('price')}
                        for key, items in json.loads(order.items).items()}
    print(details)