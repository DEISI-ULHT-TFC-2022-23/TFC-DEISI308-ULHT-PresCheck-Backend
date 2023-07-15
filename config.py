import os


class Configuration:
    # Configurações da App
    SECRET_KEY = os.environ.get('SECRET_KEY')
    ARDUINO_SECRET_KEY = os.environ.get('ARDUINO_SECRET_KEY')
    ARDUINO_AUTH_KEY = os.environ.get('ARDUINO_AUTH_KEY')

    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin'

    # Configurações da base de dados
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                                          'ulht-prescheck.db')

    # Configurações do email
    MAIL_SERVER = 'smtp.office365.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ("ULHT PresCheck", MAIL_USERNAME)
