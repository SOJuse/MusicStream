import os

user = "root"
pin = "root"
host = "localhost"
db_name = "musicstream"

app_dir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'A SECRET KEY'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEVELOPMENT_DATABASE_URI') or \
                              f"mysql+pymysql://{user}:{pin}@{host}/{db_name}"


class DevelopementConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEVELOPMENT_DATABASE_URI') or \
                              f"mysql+pymysql://{user}:{pin}@{host}/{db_name}"


class TestingConfig(BaseConfig):
    DEBUG = True
