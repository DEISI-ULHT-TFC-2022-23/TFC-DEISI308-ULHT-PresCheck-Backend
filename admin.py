from flask import Blueprint, jsonify, request
import requests
from threading import Thread

import auth
from models import *

admin = Blueprint('admin', __name__)

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


@admin.route("/admin/utilizadores", methods=["GET"])
def admin_utilizadores():
    utilizadores = [{"id": user.id,
                     "username": user.username,
                     "is_professor": True if user.professor_id else False,
                     "is_admin": user.is_admin,
                     "is_active": user.is_active}
                    for user in User.query.filter(User.id != 1).all()]
    return jsonify(utilizadores=utilizadores), 200


@admin.route("/admin/utilizadores/<int:id_user>", methods=["GET"])
def admin_utilizadores_id(id_user):
    user = User.query.get(id_user)
    if not user:
        return jsonify(error="Utilizador não encontrado"), 404

    return jsonify(username=user.username,
                   is_active=user.is_active,
                   is_admin=user.is_admin,
                   is_professor=True if user.professor_id else False,
                   unidades=user.get_associated_unidades()), 200


@admin.route("/admin/utilizadores/criar", methods=["PUT"])
def admin_utilizadores_criar():
    params = request.get_json()
    username, is_admin, is_professor, unidades = params["username"], params["admin"], params["professor"], params["unidades"]

    if not username or not is_admin or not is_professor or not unidades:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    try:
        user = User.create(username=username, is_admin=is_admin, is_professor=is_professor, unidades=unidades)
        if user[0] is False:
            return jsonify(error="O utilizador já existe."), 409

        # Envia o email para o utilizador numa thread à parte
        Thread(target=auth.send_email, args=(
            user[1].username,
            user[2],
            "ULHT PresCheck - Criação de acesso",
            "send_password.html",
            True,)).start()

        return jsonify(message="Utilizador criado com sucesso"), 200
    except Exception:
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


# TODO: Rever a arquitetura entre backend e arduino
@admin.route("/admin/alunos/associar", methods=["POST"])
def admin_alunos_associar():
    try:
        arduino_response = requests.get("http://localhost:5001/arduino")
    except ConnectionError:
        return jsonify(error="Não foi possível estabelecer ligação com o Arduino."), 500

    if arduino_response.status_code != 200:
        return jsonify(error=arduino_response.json()), arduino_response.status_code

    params = arduino_response.json()
    arduino_response.close()
    from app import Configuration
    data = jwt.decode(params['token'],
                      key=Configuration.ARDUINO_SECRET_KEY,
                      algorithms=['HS256', ])

    arduino_id, disp_uid = data["identifier"], data["uid"]
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
    except Exception:
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
    except Exception:
        return jsonify(error="Ocorreu um problema ao inserir na base de dados."), 500


@admin.route("/admin/dispositivo/eliminar/<int:aluno_id>/<string:uid>", methods=["DELETE"])
def admin_dispositivo_eliminar(aluno_id, uid):
    try:
        numero = int(aluno_id)
        deletion = Dispositivo.delete(numero, uid)

        if deletion is False:
            return jsonify(error="Não foi possível eliminar o dispositivo."), 404

        return jsonify(), 200
    except Exception:
        return jsonify(error="Ocorreu um problema ao eliminar da base de dados."), 500
