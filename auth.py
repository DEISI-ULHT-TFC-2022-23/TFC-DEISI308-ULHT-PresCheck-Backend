from flask import Blueprint, request, jsonify
from threading import Thread

from models import User

auth = Blueprint('auth', __name__)


def send_email(username, data, subject, template, demo=True):  # TODO: Mudar para False quando for para produção
    from app import app, mail
    from flask import render_template
    from flask_mail import Message
    recipient = f"{username}@ulusofona.pt" if not demo else app.config['MAIL_USERNAME']

    with app.app_context():
        msg = Message(
            subject=subject,
            recipients=[recipient],
            html=render_template(template, user=username, data=data)
        )
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
    if not login_result[0]:
        # Retorna JSON do erro
        return jsonify(error='Acesso negado. Verifique os seus dados e tente novamente. Caso tenha problemas, '
                             'contacte a Secretaria do DEISI.'), 401

    # Retorna JSON de sucesso após o ‘login’ bem-sucedido
    return jsonify(token=login_result[1].generate_session_token(), professor_id=login_result[1].professor, is_admin=login_result[1].is_admin), 200


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

    # Envia o email para o utilizador numa thread à parte
    Thread(target=send_email, args=(
        user.username,
        user.generate_reset_token(),
        "ULHT PresCheck - Recuperação",
        "reset_email.html",)).start()

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
    if not user or not user.verify_reset_token(username, token):
        # Retorna JSON do erro
        return jsonify(error='O utilizador ou o token são inválidos. Tente novamente.'), 404

    # Atualiza a password do utilizador na base de dados
    user.set_password(password, commit=True)

    # Retorna JSON de sucesso
    return jsonify(message="Senha alterada com sucesso."), 200


@auth.route("/conta/alterar-senha", methods=["POST"])
def alterar_senha():
    # Recebe os dados enviados no corpo do request
    params = request.get_json()
    username, password, new_password = params['username'], params['password'], params['new_password']

    # Verifica se os parâmetros foram recebidos
    if not username or not password or not new_password:
        # Retorna JSON do erro
        return jsonify(error='[CRITICAL] Falta parâmetros para completar o processo!'), 400

    # Verificar se o utilizador existe e retorna o objeto
    user = User.verify_user(username)

    # Verifica se o utilizador existe na base de dados e a senha fornecida está correta
    if not user or not user.verify_password(password):
        # Retorna JSON do erro
        return jsonify(error='Acesso negado. Verifique os seus dados e tente novamente. Caso tenha problemas, '
                             'contacte a Secretaria do DEISI.'), 401

    # Atualiza a password do utilizador na base de dados
    user.set_password(new_password, commit=True)

    return jsonify(message="Senha alterada com sucesso."), 200
