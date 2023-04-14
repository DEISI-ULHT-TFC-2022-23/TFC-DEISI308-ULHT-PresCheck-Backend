from flask import Flask
from models import db, User
from flask_login import LoginManager


def create_app():
    # Função para criar e configurar uma instância do aplicativo Flask

    app = Flask(__name__)

    # Configuração da chave secreta para o aplicativo
    app.config['SECRET_KEY'] = "HxmSDFCI:'Jt^!f5>}YHX3yt3Y5{oU-ULHT"

    # Configuração da URI do banco de dados SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projeto.sqlite'

    db.init_app(app)

    with app.app_context():
        # Criação das tabelas do banco de dados
        db.create_all()

    # Registro dos blueprints (módulos) no aplicativo
    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    # Configuração do LoginManager para gestão de autenticação de utilizador
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'  # Rota para login
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        # Função para carregar o utilizador com base no ID do utilizador
        return User.query.get(int(user_id))

    return app


if __name__ == '__main__':
    # Criação e execução do aplicativo Flask quando o arquivo é executado diretamente
    main_app = create_app()
    main_app.run(debug=True, port=5000, host='0.0.0.0')
