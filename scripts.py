from app.utilities import void_pickle_dumper

# void_pickle_dumper(r_type="z")
import json
from pathlib import Path
from app import app
# Read the business hours config setting data from the json file

with open(str(Path(app.root_path) / "settings" / "config.json"),
          encoding="utf8") as file:
    config = file.read()

hours = json.loads(config)[0].get('BUSINESS_HOURS')

print(hours)