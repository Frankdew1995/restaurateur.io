from app import app, db
from app.utilities import void_pickle_dumper, formatter
from pathlib import Path
import subprocess
import os
from glob import glob


def db_init():

    db.create_all()
    print("DB Init Successful!!")

def remove_qrcodes():

    qrcodes = glob(str(Path(app.root_path) / 'static' / 'qrcode' / '*.png'))

    for file in qrcodes:

        try:
            os.remove(file)

        except Exception as e:

            print(str(e))

        print(f"Removed {file}")


def remove_docx():

    docs = glob(str(Path(app.root_path) / 'static' / 'out' / 'receipts' / '*.docx'))

    pdfs = glob(str(Path(app.root_path) / 'static' / 'out' / 'receipts' / '*.pdf'))

    files = docs + pdfs

    for file in files:

        try:
            os.remove(file)

        except Exception as e:

            print(str(e))

        print(f"Removed {file}")


def install_packages():

    subprocess.call(["pip", "install", "-r", "requirements.txt"])


if __name__ == '__main__':

    # remove_qrcodes()
    # remove_docx()
    install_packages()
    print("Init finished", "初始化完成")
