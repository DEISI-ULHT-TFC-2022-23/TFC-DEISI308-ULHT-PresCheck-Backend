from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from uuid import uuid4
from models import User

auth = Blueprint('auth', __name__)


@auth.route("/login", methods=["POST"])
def login():
    username = request.json.get('username')
    password = request.json.get('password')

    # Obtém o utilizador com base no nome de utilizador fornecido
    user = User.query.filter_by(username=username).first()

    # Verifica se o usuário existe e se a senha fornecida está correta
    if not user or not check_password_hash(user.password, password):
        # Retorna JSON do erro
        return jsonify(error='Verifique os seus dados e tente novamente.'), 400

    # Verifica se o utilizador está ativo
    if not user.is_active:
        # Retorna JSON do erro
        return jsonify(error='O seu utilizador está desativado. Contate a Direção do DEISI.'), 400

    # Efetua o ‘login’ do utilizador
    token = uuid4()
    # Retorna JSON de sucesso após o ‘login’ bem-sucedido
    return jsonify(token=token, professor_id=user.professor_id), 200
