from flask import Flask
from flask_mail import Mail
from flask_cors import CORS

from config import Configuration
from admin import admin as admin_blueprint
from auth import auth as auth_blueprint
from main import main as main_blueprint
from models import db

mail = Mail()

app = Flask(__name__)
app.config.from_object(Configuration)
CORS(app)
db.init_app(app)
mail.init_app(app)

with app.app_context():
    # Criação das tabelas da base de dados
    db.create_all()

# Registro dos blueprints (módulos) na app
app.register_blueprint(main_blueprint)
app.register_blueprint(auth_blueprint)
app.register_blueprint(admin_blueprint)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
