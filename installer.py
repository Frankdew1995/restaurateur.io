from app import app
from app.utilities import void_pickle_dumper, formatter
from pathlib import Path
import subprocess
import os
from glob import glob


def remove_qrcodes():

    qrcodes = glob(str(Path(app.root_path) / 'static' / 'qrcode' / '*.png'))

    for file in qrcodes:

        try:
            os.remove(file)

        except:

            pass
        print(f"Removed {file}")


if __name__ == '__main__':

    remove_qrcodes()
