from flask import Flask
from flask_mail import Mail
from flask_cors import CORS

from config import Configuration
from admin import admin as admin_blueprint
from auth import auth as auth_blueprint
from main import main as main_blueprint
from stats import stats as stats_blueprint
from models import db, User

mail = Mail()

app = Flask(__name__)
app.config.from_object(Configuration)
CORS(app)
db.init_app(app)
mail.init_app(app)


def init_db():
    with app.app_context():
        # Criação das tabelas da base de dados
        db.create_all()
        User.create(user_id=1,
                    username=Configuration.ADMIN_USERNAME,
                    password=Configuration.ADMIN_PASSWORD,
                    is_admin=True)


# Registro dos blueprints (módulos) na app
app.register_blueprint(main_blueprint)
app.register_blueprint(auth_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(stats_blueprint)

if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=5000)

# TODO: Melhorar as condições "if" para verificar se os parâmetros são válidos e otimizar o código
# TODO: Rever a arquitetura entre backend e arduino na rota "/admin/alunos/associar"(admin) e "presencas/arduino"(main)
# TODO: Implementar encriptação dos dados de UID de dispositivo e arduino na base de dados
# TODO: Implementar JWT em todas as rotas
# TODO: Alterar os métodos HTTP para os corretos (ex: PUT para POST na criação de objetos)
# TODO: Implementar paginação nas rotas de listagem
