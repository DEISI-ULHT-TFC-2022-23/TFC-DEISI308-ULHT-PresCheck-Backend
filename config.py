import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Configuration:
    Debug = True
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'ulht-prescheck.db')
    SECRET_KEY = 'secretkey'
