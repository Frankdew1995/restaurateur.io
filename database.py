
from app.models import Order, Log, User, Table, Food
from app import db
from uuid import uuid4
import json
from datetime import datetime, timedelta
import pytz
timezone = "Europe/Berlin"

from app.models import Food

today = datetime.now(tz=pytz.timezone(timezone)).date()

tables = db.session.query(Table).all()

for table in tables:

    if not table.is_on:
        table.is_on = True
        db.session.commit()