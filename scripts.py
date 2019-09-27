from app.utilities import void_pickle_dumper, formatter

import json
from pathlib import Path
from app import app, db
from app.models import Order, Table
from datetime import datetime, timedelta
import subprocess
import os
import pickle

from app.utilities import eat_manner_pickler, void_pickle_dumper

void_pickle_dumper(r_type="x")

