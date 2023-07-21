from concurrent.futures import ThreadPoolExecutor

import jwt
import requests
from flask import Flask
from flask_cors import CORS
from flask_mail import Mail

from admin import admin as admin_blueprint
from auth import auth as auth_blueprint
from config import Configuration
from main import main as main_blueprint
from models import db, User
from stats import stats as stats_blueprint

mail = Mail()

app = Flask(__name__)
app.config.from_object(Configuration)
CORS(app,
     origins="*",
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"])
db.init_app(app)
mail.init_app(app)

executor = ThreadPoolExecutor()


def acao_arduino(ip_address, acao):
    token = jwt.encode({"identifier": Configuration.ARDUINO_AUTH_KEY},
                       key=Configuration.ARDUINO_SECRET_KEY,
                       algorithm='HS256')
    with requests.Session() as session:
        try:
            arduino_response = session.get(f"http://{ip_address}:5001/arduino/{acao}",
                                           headers={"Authorization": f"Bearer {token}"})
            arduino_response.raise_for_status()
            return arduino_response.json()
        except requests.exceptions.RequestException as e:
            print(e)
            return {"error": "Não foi possível estabelecer ligação com o Arduino"}, 500


with app.app_context():
    db.create_all()
    User.create(user_id=1,
                username=Configuration.ADMIN_USERNAME,
                password=Configuration.ADMIN_PASSWORD,
                is_admin=True)

app.register_blueprint(main_blueprint)
app.register_blueprint(auth_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(stats_blueprint)

if __name__ == "__main__":
    try:
        print("A iniciar o servidor...")
        app.run(host='0.0.0.0', port=5000)
    finally:
        print("A encerrar o servidor...")
        executor.shutdown(wait=True)
        exit(0)
