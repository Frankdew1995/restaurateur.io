from app import app, db
from app.utilities import void_pickle_dumper, json_reader
from pathlib import Path
import subprocess
import os
from glob import glob
import json
import random
import string
from uuid import uuid4
import time


def random_user_string(length):

    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))


def random_password_string(length):

    password_characters = string.ascii_letters + string.digits + string.punctuation

    return ''.join(random.choice(password_characters) for i in range(length))


def ngrok_init(bit_version):

    settings = json_reader(str(Path(app.root_path) / 'settings' / 'credentials.json'))

    auth = settings.get('NGROK_AUTH')

    executable = str(Path(app.root_path) / 'utils' / 'ngrok' / str(bit_version) / 'ngrok')

    subprocess.call([executable, 'authtoken', auth])

    print("ngrok authentification complete")


def db_init():

    db.create_all()
    print("DB Init Successful!!", "数据库初始化完成")


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
    print("All packages installed", "全部依赖包完成安装")


def create_superuser():

    from app.models import User

    username = random_user_string(10)
    alias = u"老板"
    password = random_password_string(10)

    # By default permission for boss account is 100
    permissions = 100

    user = User(username=username,
                alias=alias,
                container=json.dumps({'inUse': True}),
                permissions=permissions,
                email=f"{str(uuid4())}@cnfrien.com")

    user.set_password(password=password)

    db.session.add(user)

    db.session.commit()

    print("Super User created", "老板账号创建完成", username)

    print("Super User password created", "老板账号密码创建完成", password)


if __name__ == '__main__':

    remove_qrcodes()
    remove_docx()
    # install_packages()
    # ngrok_init(bit_version=32)
    void_pickle_dumper(r_type="Z")
    void_pickle_dumper(r_type="X")
    # db_init()
    print("Z,X cache data cleared!!", "Z单，X单缓存数据清理完成!")
    print("Init finished", "所有初始化完成")
    # create_superuser()
    time.sleep(3600)