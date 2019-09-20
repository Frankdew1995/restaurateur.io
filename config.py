import os

cur_path = os.path.dirname(__file__)

basedir = os.path.abspath(cur_path)

class Config(object):

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or\
                              'sqlite:///' + os.path.join(basedir, 'app.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = False

    CACHE_TYPE = "simple"

class DevConfig(Config):

    pass
