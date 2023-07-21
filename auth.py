from threading import Thread

from flask import Blueprint, request, jsonify

from models import User

auth = Blueprint('auth', __name__)


def send_email(username, data, subject, template, demo=True):
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
    params = request.get_json()
    username, password = params['username'], params['password']

    if not username or not password:
        return jsonify(error='[CRITICAL] Falta parâmetros para completar o processo!'), 400

    login_result = User.login_user(username, password)
    if not login_result[0]:
        return jsonify(error='Acesso negado. Verifique os seus dados e tente novamente. Caso tenha problemas, '
                             'contacte a Secretaria do DEISI.'), 401

    return jsonify(token=login_result[1].generate_session_token(), professor_id=login_result[1].professor_id,
                   is_admin=login_result[1].is_admin), 200


@auth.route("/recuperar", methods=["POST"])
def recuperar_senha():
    params = request.get_json()
    username = params['username']

    if not username:
        return jsonify(error='[CRITICAL] Falta parâmetros para completar o processo!'), 400

    user = User.verify_user(username)
    if not user:
        return jsonify(error='O utilizador não existe. Contacte a Secretaria do DEISI.'), 404

    Thread(target=send_email, args=(
        user.username,
        user.generate_reset_token(),
        "ULHT PresCheck - Recuperação",
        "reset_password.html",)).start()

    return jsonify(message="Email enviado com sucesso."), 200


@auth.route("/recuperar/alterar", methods=["POST"])
def recuperar_senha_alterar():
    params = request.get_json()
    username, password, token = params['username'], params['password'], params['token']

    if not username or not password or not token:
        return jsonify(error='[CRITICAL] Falta parâmetros para completar o processo!'), 400

    user = User.verify_user(username)
    if not user or not user.verify_reset_token(username, token):
        return jsonify(error='O utilizador ou o token são inválidos. Tente novamente.'), 404

    user.set_password(password, commit=True)
    return jsonify(message="Senha alterada com sucesso."), 200
