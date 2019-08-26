
from app.models import Order
from app import db
from uuid import uuid4
import json
from datetime import datetime
import pytz
timezone = "Europe/Berlin"

today = datetime.now(tz=pytz.timezone(timezone)).date()


orders = db.session.query(Order).filter(
                        Order.type == "In").order_by(Order.timeCreated.desc()).all()

# order = orders[0]
#
# if order.timeCreated.date() == today:
#
#     cur_items = json.loads(order.items)
#
#     dishes = order.dishes
#
#     if not dishes:
#
#         dishes = []
#         print(dishes)
#
#     else:
#
#         dishes = json.loads(order.dishes)
#
#     new_items = {'Gongbao JiDing':
#                      {'quantity': 3,
#                         'price': 22.0,
#                         'class_name': 'Food',
#                         "ordered_by": "10"},
#
#                  "Hot Pot": {
#                      "quantity": 1,
#                      "price": 55,
#                      "class_name": "Food",
#                      "ordered_by": "10"}
#     }
#
#     dishes.append(new_items)
#
#     order.dishes = json.dumps(dishes)
#
#     cur_dishes = cur_items.keys()
#
#     for dish, items in new_items.items():
#
#         if dish in cur_dishes:
#
#             cur_items[dish]['quantity'] = cur_items[dish]['quantity'] + items.get('quantity')
#
#         else:
#
#             cur_items[dish] = items
#
#     order.items = json.dumps(cur_items)
#
#     order.totalPrice = sum([i[1].get('quantity')*i[1].get('price') for i in cur_items.items()])
#
#     db.session.commit()
#
