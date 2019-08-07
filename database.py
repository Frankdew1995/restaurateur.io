from app.models import User, Order, Log
from pathlib import Path

from datetime import datetime

from app import db, app

import json

import pandas as pd



logs = Log.query.all()

print(logs)