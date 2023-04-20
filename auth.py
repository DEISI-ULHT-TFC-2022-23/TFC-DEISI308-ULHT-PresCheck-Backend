from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from uuid import uuid4
from models import User

auth = Blueprint('auth', __name__)


@auth.route("/login", methods=["POST"])
def login():
    # Recebe os dados enviados no corpo do request
    username = request.json.get('username')
    password = request.json.get('password')

    # Verifica se os parâmetros foram recebidos
    if not username or not password:
        # Retorna JSON do erro
        return jsonify(error='[CRITICAL] Falta parâmetros para completar o processo!'), 400

    # Obtém o utilizador com base no nome de utilizador fornecido
    user = User.query.filter_by(username=username).first()

    # Verifica se o utilizador existe e se a senha fornecida está correta
    if not user or not check_password_hash(user.password, password):
        # Retorna JSON do erro
        return jsonify(error='Credenciais inválidas. Verifique os seus dados e tente novamente.'), 401

    # Verifica se o utilizador está ativo
    if not user.is_active:
        # Retorna JSON do erro
        return jsonify(error='O seu utilizador está desativado. Contacte a Secretaria do DEISI.'), 403

    # Cria o token de sessão do utilizador
    token = uuid4()
    # Retorna JSON de sucesso após o ‘login’ bem-sucedido
    return jsonify(token=token, professor_id=user.professor_id, is_admin=user.is_admin), 200
