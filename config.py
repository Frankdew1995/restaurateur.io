import os

cur_path = os.path.dirname(__file__)

basedir = os.path.abspath(cur_path)

mongo_pass = os.environ.get('MONGO_ACCESS')


class Config(object):

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or\
                              'sqlite:///' + os.path.join(basedir, 'app.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MONGO_URI = f"mongodb://frankdew1995:ABnt5nEZdvsCR52@ds113936.mlab.com:13936/testdatabase"


class DevConfig(Config):

    pass
