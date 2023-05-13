import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Configuration:
    # Configurações da App
    Debug = True
    SECRET_KEY = 'secretkey'

    # Configurações da base de dados
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'ulht-prescheck.db')

    # Configurações do email
    MAIL_SERVER = 'smtp.office365.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'ulht-prescheck@outlook.pt'
    MAIL_PASSWORD = 'TFC_lusofona.2023'
    MAIL_DEFAULT_SENDER = ("ULHT PresCheck", "ulht-prescheck@outlook.pt")

