from flask import Blueprint, request, jsonify
from flask_mail import Message
from uuid import uuid4
from threading import Thread

from models import User

auth = Blueprint('auth', __name__)


def send_email(msg):
    from app import app, mail
    with app.app_context():
        mail.send(msg)


@auth.route("/login", methods=["POST"])
def login():
    # Recebe os dados enviados no corpo do request
    params = request.get_json()
    username, password = params['username'], params['password']

    # Verifica se os parâmetros foram recebidos
    if not username or not password:
        # Retorna JSON do erro
        return jsonify(error='[CRITICAL] Falta parâmetros para completar o processo!'), 400

    # Realiza a ação de login do utilizador
    login_result = User.login_user(username, password)

    # Verifica se o utilizador existe e se a senha fornecida está correta
    if not login_result:
        # Retorna JSON do erro
        return jsonify(error='Acesso negado. Verifique os seus dados e tente novamente. Caso tenha problemas, '
                             'contacte a Secretaria do DEISI.'), 401

    # Cria o token de sessão do utilizador
    token = uuid4()

    # Retorna JSON de sucesso após o ‘login’ bem-sucedido
    return jsonify(token=token, professor_id=login_result[1]['professor_id'], is_admin=login_result[1]['is_admin']), 200


@auth.route("/recuperar", methods=["POST"])
def recuperar_senha():
    # Recebe os dados enviados no corpo do request
    params = request.get_json()
    username = params['username']

    # Verifica se os parâmetros foram recebidos
    if not username:
        # Retorna JSON do erro
        return jsonify(error='[CRITICAL] Falta parâmetros para completar o processo!'), 400

    # Verificar se o utilizador existe e retorna o objeto
    user = User.verify_user(username)

    # Verifica se o utilizador existe na base de dados
    if not user:
        # Retorna JSON do erro
        return jsonify(error='O utilizador não existe. Contacte a Secretaria do DEISI.'), 404

    # Prepara o objeto de mensagem de email
    msg = Message()
    msg.subject = "ULHT PresCheck - Recuperar senha"
    msg.recipients = ["alexandre.nunes.garcia10@gmail.com"]
    from flask import render_template
    msg.html = render_template('reset_email.html', user=user.username, token=user.get_reset_token())
    # Envia o email para o utilizador numa thread à parte
    Thread(target=send_email, args=(msg, )).start()

    # Retorna JSON de sucesso
    return jsonify(message="Email enviado com sucesso."), 200


@auth.route("/recuperar/alterar", methods=["POST"])
def recuperar_senha_alterar():
    # Recebe os dados enviados no corpo do request
    params = request.get_json()
    username, password, token = params['username'], params['password'], params['token']

    # Verifica se os parâmetros foram recebidos
    if not username or not password or not token:
        # Retorna JSON do erro
        return jsonify(error='[CRITICAL] Falta parâmetros para completar o processo!'), 400

    # Verificar se o utilizador existe e retorna o objeto
    user = User.verify_user(username)

    # Verifica se o utilizador existe na base de dados e o token está correto
    if not user or not user.verify_reset_token(token):
        # Retorna JSON do erro
        return jsonify(error='O utilizador ou o token são inválidos. Tente novamente.'), 404

    # Atualiza a password do utilizador na base de dados
    user.set_password(password, commit=True)

    # Retorna JSON de sucesso
    return jsonify(message="Senha alterada com sucesso."), 200
