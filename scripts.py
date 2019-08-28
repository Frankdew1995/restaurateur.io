

data = [
        {1: {"lastPrinted": "2013.09.20"}},
        {2: {"lastPrinted": "2013.09.21"}}
    ]

print(data)


import pytz
timezone = "Europe/Berlin"
from datetime import datetime

now = datetime.now(pytz.timezone(timezone))

print(datetime.timestamp(now))