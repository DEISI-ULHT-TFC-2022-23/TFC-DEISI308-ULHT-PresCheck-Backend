import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Configuration:
    # Configurações da App
    Debug = True
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Configurações da base de dados
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'ulht-prescheck.db')

    # Configurações do email
    MAIL_SERVER = 'smtp.office365.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ("ULHT PresCheck", MAIL_USERNAME)
