from app.utilities import void_pickle_dumper, formatter

# void_pickle_dumper(r_type="z")
import json
from pathlib import Path
from app import app, db
from app.models import Order, Table
from datetime import datetime, timedelta
import subprocess
import os
import pickle

with open(str(Path(app.root_path) / 'cache' / 'z_bon_settings.pickle'),
          mode="rb") as pickle_out:
    data = pickle.load(pickle_out)


now = datetime.now().timestamp()


def is_z_printed(timestamp):

    with open(str(Path(app.root_path) / 'cache' / 'z_bon_settings.pickle'),
              mode="rb") as pickle_out:

        data = pickle.load(pickle_out)

    printed_timestamps = []

    for record in data:

        print(record)

        key = list(record.keys())[0]

        last_printed = record.get(key).get('lastPrinted')
        last_timestamp = last_printed.timestamp()
        printed_timestamps.append(last_timestamp)

    return timestamp in printed_timestamps

print(is_z_printed(now))