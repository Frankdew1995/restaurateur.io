from app.utilities import void_pickle_dumper, formatter

# void_pickle_dumper(r_type="z")
import json
from pathlib import Path
from app import app, db
from app.models import Order
from datetime import datetime, timedelta
import subprocess
import os
seat_number = "1"

orders = db.session.query(Order).filter(
        Order.type == "In",
        Order.isPaid == False,
        Order.isCancelled == False,
        Order.subtype == "jpbuffet",
        Order.table_name == "A1").order_by(Order.timeCreated.desc()).all()

token = "5cXKkSkzt3Pyf7NuwKBb1_5nry6JWt3mwFtcYN8M3Hw"
path = str(Path(app.root_path) / 'utils' / "ngrok 32")

def run_ngrok(path, port, auth):

        os.chdir(path)
        # ngrok auth
        subprocess.Popen(f"ngrok authtoken {auth}")
        subprocess.Popen(["ngrok", "http", "-region=eu", f"{port}"])
