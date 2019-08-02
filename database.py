from app.models import User, Order


from datetime import datetime

from app import db

import json

users = db.session.query(User).all()

orders = Order.query.all()






# for order in orders:
#
#     for time in time_objects:
#
#         print(order.timeCreated.time() < time)


print(datetime.now().time())