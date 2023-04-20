import os

from flask import Flask
from flask_cors import CORS

from admin import admin as admin_blueprint
from auth import auth as auth_blueprint
from main import main as main_blueprint
from models import db

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
CORS(app)

# Configuração da chave secreta para a aplicação
app.config['SECRET_KEY'] = "HxmSDFCI:'Jt^!f5>}YHX3yt3Y5{oU-ULHT"

# Configuração da URI da base de dados SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ulht-prescheck.db')

db.init_app(app)

with app.app_context():
    # Criação das tabelas da base de dados
    db.create_all()

# Registro dos blueprints (módulos) na app
app.register_blueprint(main_blueprint)
app.register_blueprint(auth_blueprint)
app.register_blueprint(admin_blueprint)

if __name__ == "__main__":
    app.run()
