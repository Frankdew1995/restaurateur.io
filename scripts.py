from app.utilities import void_pickle_dumper, formatter

import json
from pathlib import Path
from app import app, db
from app.models import Order, Table
from datetime import datetime, timedelta
import subprocess
import os
import pickle

from app.utilities import void_pickle_dumper, print_qrcode

void_pickle_dumper(r_type="z")

# print_qrcode()