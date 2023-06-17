from flask import Blueprint, jsonify, request
import requests

import auth
from models import *

admin = Blueprint('admin', __name__)

demo_username = "demo"
demo_password = "demo"


# @admin.before_request
# def before_request():
#     authorization_header = request.headers.get("Authorization")
#     if not authorization_header or not authorization_header.startswith("Bearer "):
#         return jsonify(error="Não autorizado"), 401
#
#     token = authorization_header.split(" ")[1]
#     if not token:
#         return jsonify(error="Não autorizado"), 401
#
#     user = User.verify_session_token(token)
#     if not user:
#         return jsonify(error="Não autorizado"), 401
#
#     if user['active'] is False or user["admin"] is False:
#         return jsonify(error="Não autorizado"), 401


@admin.route("/admin/demo/criar", methods=["GET"])
def admin_demo_criar():
    user = User.create(demo_username, demo_password, True, True)
    unidades = [Unidade.create(15151, "Matemática")[1], Unidade.create(1048294, "Segurança Informática")[1]]
    professor = Professor.create(1, unidades)
    user[1].associate_prof(1, commit=True)
    sala = Sala.create("F.2.3", "123")
    return jsonify(username=user[1].username, password=demo_password, is_admin=user[1].is_admin,
                   professor_id=professor[1].id, unidades=Professor.get_unidades(professor[1].id),
                   sala=sala[1].nome), 200


@admin.route("/admin/utilizadores", methods=["GET"])
def admin_utilizadores():
    # retora todos os utilizadores exceto o admin
    utilizadores = [{"username": user.username,
                     "is_professor": True if user.professor_id else False,
                     "is_admin": user.is_admin,
                     "is_active": user.is_active}
                    for user in User.query.filter(User.id != 1).all()]
    return jsonify(utilizadores=utilizadores), 200


@admin.route("/admin/utilizadores/<int:id_user>", methods=["GET"])
def admin_utilizadores_id(id_user):
    # retorna um utilizador específico
    user = User.query.get(id_user)
    if not user:
        return jsonify(error="Utilizador não encontrado"), 404

    return jsonify(username=user.username,
                   is_active=user.is_active,
                   is_professor=True if user.professor_id else False,
                   unidades=user.get_associated_unidades()), 200


@admin.route("/admin/utilizadores/criar", methods=["PUT"])
def admin_utilizadores_criar():
    params = request.get_json()
    username, is_admin, is_professor, unidades = params["username"], params["admin"], params["professor"], params[
        "unidades"]
    if not username or is_admin is None or is_professor is None:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    try:
        unidades = [int(unidade) for unidade in unidades if unidades != ""]
        user = User.create(username, is_admin, True, is_professor, unidades)

        if user[0] is False:
            return jsonify(error="O utilizador já existe."), 409

        from flask import render_template
        from threading import Thread
        from flask_mail import Message
        msg = Message(
            subject="ULHT PresCheck - Criação de acesso",
            recipients=[f"{username}@ulusofona.pt"],
            html=render_template('send_password.html', user=username, password=user[1].password)
        )
        # Envia o email para o utilizador numa thread à parte
        Thread(target=auth.send_email, args=(msg,)).start()

        return jsonify(message="Utilizador criado com sucesso"), 200
    except Exception as e:
        print(e)
        return jsonify(error="Ocorreu um problema ao inserir na base de dados."), 500


@admin.route("/admin/alunos", methods=["GET"])
def admin_alunos():
    alunos = [{"numero": aluno.id, "dispositivos": len(aluno.dispositivos)} for aluno in Aluno.query.all()]
    alunos = sorted(alunos, key=lambda k: k['numero'])
    return jsonify(alunos=alunos), 200


@admin.route("/admin/alunos/<int:aluno_id>", methods=["GET"])
def admin_alunos_id(aluno_id):
    aluno = Aluno.query.get(aluno_id)
    if not aluno:
        return jsonify(error="Aluno não encontrado"), 404

    dispositivos = [{"uid": dispositivo.uid, "associado_em": dispositivo.created_at} for dispositivo in
                    aluno.dispositivos]
    ultimas_presencas = aluno.get_last_classes()
    return jsonify(aluno=aluno.id, dispositivos=dispositivos, ultimas_presencas=ultimas_presencas), 200


@admin.route("/admin/alunos/associar", methods=["POST"])
def admin_alunos_associar():
    arduino_response = requests.get("http://localhost:5001/arduino")
    if arduino_response.status_code != 200:
        return jsonify(error=arduino_response.content), arduino_response.status_code

    params = arduino_response.json()
    arduino_id, disp_uid = params["identifier"], params["uid"]
    if not arduino_id or not disp_uid:
        return jsonify(error="Arduino não encontrado"), 404

    arduino = Sala.get_sala_by_arduino(arduino_id)
    if not arduino:
        return jsonify(error="O arduino não está associado a nenhuma sala."), 404

    return jsonify(uid=disp_uid), 200


@admin.route("/admin/alunos/criar", methods=["PUT"])
def admin_alunos_criar():
    params = request.get_json()
    numero, dispositivo = params["numero"], params["dispositivo"]
    if not numero:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    try:
        numero = int(numero)
        aluno = Aluno.create(numero)

        if aluno[0] is False:
            return jsonify(error="Aluno já existente"), 409

        if dispositivo is not None:
            Dispositivo.create(dispositivo, aluno[1].id)

        return jsonify(message="Aluno criado com sucesso"), 200
    except ValueError:
        return jsonify(error="Número de aluno inválido"), 400
    except Exception as e:
        print(e)
        return jsonify(error="Ocorreu um problema ao inserir na base de dados."), 500


@admin.route("/admin/alunos/eliminar/<int:aluno_id>", methods=["DELETE"])
def admin_alunos_eliminar(aluno_id):
    try:
        numero = int(aluno_id)
        deletion = Aluno.delete(numero)

        if deletion is False:
            return jsonify(error="Aluno não encontrado"), 404

        return jsonify(), 200
    except ValueError:
        return jsonify(error="Número de aluno inválido"), 400
    except Exception:
        return jsonify(error="Ocorreu um problema ao eliminar da base de dados."), 500


@admin.route("/admin/dispositivo/criar", methods=["PUT"])
def admin_dispositivo_criar():
    params = request.get_json()
    dispositivo, aluno_id = params["dispositivo"], params["aluno_id"]
    if not dispositivo or not aluno_id:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    try:
        number = int(aluno_id)
        creation = Dispositivo.create(dispositivo, number)
        if creation[0] is False:
            return jsonify(error="Dispositivo já existente"), 409

        return jsonify(), 200
    except Exception as e:
        print(e)
        return jsonify(error="Ocorreu um problema ao inserir na base de dados."), 500


@admin.route("/admin/dispositivo/eliminar/<int:aluno_id>/<string:uid>", methods=["DELETE"])
def admin_dispositivo_eliminar(aluno_id, uid):
    try:
        numero = int(aluno_id)
        deletion = Dispositivo.delete(numero, uid)

        if deletion is False:
            return jsonify(error="Não foi possível eliminar o dispositivo."), 404

        return jsonify(), 200
    except Exception as e:
        print(e)
        return jsonify(error="Ocorreu um problema ao eliminar da base de dados."), 500
