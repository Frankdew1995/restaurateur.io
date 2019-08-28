
from app.models import Order, Log
from app import db
from uuid import uuid4
import json
from datetime import datetime
import pytz
timezone = "Europe/Berlin"

today = datetime.now(tz=pytz.timezone(timezone)).date()


for log in db.session.query(Log).all():

    if str(today) in log.time:

        db.session.delete(log)
        db.session.commit()
