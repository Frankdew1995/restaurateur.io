
from app.models import User, Visit, Order, Food
from app import app, db

from app.utilities import receipt_templating


details = {
    "Coffee": 12,
    "Noodle": 23,
    "Soup": 123
}




receipt_templating(
    context={"details": details,
             "company_name": "xstar",
             "address": "maxmann strasse",
             "now": "2018 12 33 12:00:00",
             "tax_id": "121731723",
             "table_name": "34",
             "order_id": 23,
             "total": 455,
             "pay_via": "KARTE",
             "VAT": round((455 / 1.19)*0.19, 2)
             })