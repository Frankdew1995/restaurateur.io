from app.utilities import void_pickle_dumper

void_pickle_dumper(r_type="z")



from app import app
from pathlib import Path
import pickle
from datetime import datetime

with open(str(Path(app.root_path) / 'cache' / 'z_bon_settings.pickle'),
          mode="rb") as pickle_out:
    data = pickle.load(pickle_out)


dtime = list(data[-1].items())[0][1]

print(dtime)