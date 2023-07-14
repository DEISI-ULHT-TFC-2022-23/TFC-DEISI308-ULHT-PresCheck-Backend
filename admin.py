from flask import Blueprint, jsonify, request
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
    utilizadores = [{"username": user.username,
                     "is_professor": True if user.professor_id else False,
                     "is_admin": user.is_admin,
                     "is_active": user.is_active}
                    for user in User.query.filter(User.id != 1).all()]
    return jsonify(utilizadores=utilizadores), 200


@admin.route("/admin/utilizadores/<string:username>", methods=["GET"])
def admin_utilizadores_username(username):
    user = User.verify_user(username=username)
    if not user:
        return jsonify(error="Utilizador não encontrado"), 404

    return jsonify(username=user.username,
                   is_active=user.is_active,
                   is_admin=user.is_admin,
                   is_professor=True if user.professor_id else False,
                   unidades=user.get_associated_unidades(),
                   turmas=user.get_associated_turmas()), 200


@admin.route("/admin/utilizadores/criar", methods=["PUT"])
def admin_utilizadores_criar():
    params = request.get_json()
    username, is_admin, is_professor, unidades, turmas = params["username"], params["admin"], params["professor"], \
    params[
        "unidades"], params["turmas"]

    if not username or unidades is None or is_admin is None or is_professor is None:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    try:
        user = User.create(username=username, is_admin=is_admin, is_professor=is_professor, unidades=unidades,
                           turmas=turmas)
        if not user[0]:
            return jsonify(error="O utilizador já existe."), 409

        from threading import Thread
        from auth import send_email
        Thread(target=send_email, args=(
            user[1].username,
            user[2],
            "ULHT PresCheck - Criação de acesso",
            "send_password.html",)).start()

        return jsonify(message="Utilizador criado com sucesso"), 200
    except Exception:
        return jsonify(error="Ocorreu um problema ao inserir na base de dados."), 500


@admin.route("/admin/utilizadores/editar/<string:username>", methods=["PUT"])
def admin_utilizadores_editar(username):
    params = request.get_json()
    is_admin, is_active = params["admin"], params["active"]

    if is_admin is None or is_active is None:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    user = User.verify_user(username=username)
    if not user:
        return jsonify(error="Utilizador não encontrado"), 404

    user.update(is_admin=is_admin, is_active=is_active, commit=True)
    return jsonify(message="Utilizador editado com sucesso"), 200


@admin.route("/admin/utilizadores/<string:username>/unidades/associar", methods=["POST"])
def admin_utilizadores_unidades_associar(username):
    params = request.get_json()
    unidades = params["unidades"]

    if unidades is None:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    user = User.verify_user(username=username)
    if not user or user.professor_id is None:
        return jsonify(error="Utilizador não encontrado ou não é professor"), 404

    user_prof = user.get_professor()
    user_prof.associate_unidades(unidades=unidades, commit=True)

    return jsonify(message="Unidades associadas com sucesso"), 200


@admin.route("/admin/utilizadores/<string:username>/unidades/eliminar/<int:unidade_id>", methods=["DELETE"])
def admin_utilizadores_unidades_eliminar(username, unidade_id):
    user = User.verify_user(username=username)
    if not user or user.professor_id is None:
        return jsonify(error="Utilizador não encontrado ou não é professor"), 404

    user_prof = user.get_professor()
    user_prof.remove_unidade(unidade_id=unidade_id, commit=True)

    return jsonify(message="Unidades associadas com sucesso"), 200


@admin.route("/admin/utilizadores/<string:username>/turmas/associar", methods=["POST"])
def admin_utilizadores_turmas_associar(username):
    params = request.get_json()
    turmas = params["turmas"]

    if turmas is None:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    user = User.verify_user(username=username)
    if not user or user.professor_id is None:
        return jsonify(error="Utilizador não encontrado ou não é professor"), 404

    user_prof = user.get_professor()
    user_prof.associate_turmas(turmas=turmas, commit=True)

    return jsonify(message="Turmas associadas com sucesso"), 200


@admin.route("/admin/utilizadores/<string:username>/turmas/eliminar/<int:turma_id>", methods=["DELETE"])
def admin_utilizadores_turmas_eliminar(username, turma_id):
    user = User.verify_user(username=username)
    if not user or user.professor_id is None:
        return jsonify(error="Utilizador não encontrado ou não é professor"), 404

    user_prof = user.get_professor()
    user_prof.remove_turma(turma_id=turma_id, commit=True)

    return jsonify(message="Turmas associadas com sucesso"), 200


@admin.route("/admin/turmas", methods=["GET"])
def admin_turmas():
    turmas = [{"id": turma.id, "nome": turma.nome, "alunos": len(turma.alunos)} for turma in Turma.query.all()]
    return jsonify(turmas=turmas), 200


@admin.route("/admin/turmas/<int:turma_id>", methods=["GET"])
def admin_turmas_id(turma_id):
    turma = Turma.query.get(turma_id)

    if turma is None:
        return jsonify(error="Turma não encontrada"), 404

    alunos = [aluno.id for aluno in turma.alunos]
    professores = [f"p{professor.id}" for professor in turma.professores]
    return jsonify(turma=turma.id, nome=turma.nome, professores=professores, alunos=alunos), 200


@admin.route("/admin/turmas/criar", methods=["POST"])
def admin_turmas_criar():
    params = request.get_json()
    nome = params["nome"]

    if not nome:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    turma = Turma.create(nome)
    if not turma[0]:
        return jsonify(error="A turma já existe."), 409

    return jsonify(message="Turma criada com sucesso"), 200


@admin.route("/admin/turmas/editar/<int:turma_id>", methods=["PUT"])
def admin_turmas_editar(turma_id):
    params = request.get_json()
    nome = params["nome"]

    if not nome:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    turma = Turma.query.get(turma_id)
    if not turma:
        return jsonify(error="Turma não encontrada"), 404

    update = turma.update(nome=nome, commit=True)
    if not update:
        return jsonify(error="Uma turma já existe com pelo menos um dos campos alterados."), 409

    return jsonify(message="Turma editada com sucesso"), 200


@admin.route("/admin/turmas/eliminar/<int:turma_id>", methods=["DELETE"])
def admin_turmas_eliminar(turma_id):
    deletion = Turma.delete(turma_id)
    if not deletion:
        return jsonify(error="Não foi possível eliminar a turma."), 409

    return jsonify(message="Turma eliminada com sucesso"), 200


@admin.route("/admin/alunos", methods=["GET"])
def admin_alunos():
    alunos = [{"numero": aluno.id, "turma": aluno.get_turma_name(), "dispositivos": len(aluno.dispositivos)}
              for aluno in Aluno.query.all()]
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
    return jsonify(aluno=aluno.id, turma=aluno.get_turma_name(), dispositivos=dispositivos, ultimas_presencas=ultimas_presencas), 200


@admin.route("/admin/alunos/associar", methods=["POST"])
def admin_alunos_associar():
    params = request.get_json()
    sala = params["sala"]

    if not sala:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    arduino = Arduino.get_arduino_by_sala("nome", sala)
    if not arduino:
        return jsonify(error="Arduino não encontrado"), 404

    from app import Configuration, acao_arduino
    json = acao_arduino(arduino.ip_address, "registo")
    data = jwt.decode(json['token'],
                      key=Configuration.ARDUINO_SECRET_KEY,
                      algorithms=['HS256', ])

    arduino_id, disp_uid = data["identifier"], data["uid"]
    return jsonify(uid=disp_uid), 200


@admin.route("/admin/alunos/criar", methods=["PUT"])
def admin_alunos_criar():
    params = request.get_json()
    numero, dispositivo, turma = params["numero"], params["dispositivo"], params["turma"]
    if not numero or not turma:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    try:
        numero = int(numero)
        aluno = Aluno.create(numero, turma)

        if not aluno[0]:
            return jsonify(error="Aluno já existente"), 409

        if dispositivo:
            Dispositivo.create(dispositivo, aluno[1].id)

        return jsonify(message="Aluno criado com sucesso"), 200
    except ValueError:
        return jsonify(error="Número de aluno inválido"), 400
    except Exception:
        return jsonify(error="Ocorreu um problema ao inserir na base de dados."), 500


@admin.route("/admin/alunos/editar/<int:aluno_id>", methods=["PUT"])
def admin_alunos_editar(aluno_id):
    params = request.get_json()
    turma = params["turma"]
    if not turma:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    try:
        aluno = Aluno.query.get(aluno_id)
        if not aluno:
            return jsonify(error="Aluno não encontrado"), 404

        update = aluno.update(turma=turma, commit=True)
        if not update:
            return jsonify(error="A turma atribuida está inválida."), 409

        return jsonify(message="Aluno editado com sucesso"), 200
    except Exception:
        return jsonify(error="Ocorreu um problema a editar na base de dados."), 500


@admin.route("/admin/alunos/eliminar/<int:aluno_id>", methods=["DELETE"])
def admin_alunos_eliminar(aluno_id):
    try:
        deletion = Aluno.delete(aluno_id)

        if not deletion:
            return jsonify(error="Aluno não encontrado"), 404

        return jsonify(), 200
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
        if not creation[0]:
            return jsonify(error="Dispositivo já existente"), 409

        return jsonify(), 200
    except Exception:
        return jsonify(error="Ocorreu um problema ao inserir na base de dados."), 500


@admin.route("/admin/dispositivo/eliminar/<int:aluno_id>/<string:uid>", methods=["DELETE"])
def admin_dispositivo_eliminar(aluno_id, uid):
    try:
        deletion = Dispositivo.delete(aluno_id, uid)

        if not deletion:
            return jsonify(error="Não foi possível eliminar o dispositivo."), 404

        return jsonify(), 200
    except Exception:
        return jsonify(error="Ocorreu um problema ao eliminar da base de dados."), 500


@admin.route("/admin/unidades", methods=["GET"])
def admin_unidades():
    unidades = [{"id": unidade.id, "nome": unidade.nome, "codigo": unidade.codigo} for unidade in Unidade.query.all()]
    return jsonify(unidades=unidades), 200


@admin.route("/admin/unidades/<string:codigo>", methods=["GET"])
def admin_unidades_id(codigo):
    unidade = Unidade.query.filter_by(codigo=codigo).first()

    if not unidade:
        return jsonify(error="Unidade não encontrada"), 404

    professores = [f"p{professor.id}"
                   for professor
                   in Professor.query.join(Professor.unidades).filter(Unidade.id == unidade.id).all()]

    return jsonify(id=unidade.id, codigo=unidade.codigo, nome=unidade.nome, professores=professores), 200


@admin.route("/admin/unidades/criar", methods=["POST"])
def admin_unidades_criar():
    params = request.get_json()
    codigo, nome = params["codigo"], params["nome"]
    if not codigo or not nome:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    try:
        unidade = Unidade.create(codigo, nome)
        if not unidade[0]:
            return jsonify(error="Unidade já existente"), 409

        return jsonify(message="Unidade criada com sucesso"), 200
    except Exception:
        return jsonify(error="Ocorreu um problema ao inserir na base de dados."), 500


@admin.route("/admin/unidades/eliminar/<int:unidade_id>", methods=["DELETE"])
def admin_unidades_eliminar(unidade_id):
    try:
        unidade = Unidade.delete(unidade_id)
        if not unidade:
            return jsonify(error="Unidade não encontrada"), 404

        return jsonify(), 200
    except Exception:
        return jsonify(error="Ocorreu um problema ao eliminar da base de dados."), 500


@admin.route("/admin/salas", methods=["GET"])
def admin_salas():
    salas = [{"id": sala.id, "nome": sala.nome, "arduino": sala.arduino_id} for sala in Sala.query.all()]
    return jsonify(salas=salas), 200


@admin.route("/admin/salas/criar", methods=["POST"])
def admin_salas_criar():
    params = request.get_json()
    nome, arduino_id, ip_address = params["nome"], params["arduino"], params["ip_address"]
    if not nome or not arduino_id or not ip_address:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    try:
        sala = Sala.create(nome)
        if not sala[0]:
            return jsonify(error="Sala já existente"), 409

        arduino = Arduino.create(arduino_id, ip_address, sala[1].id)
        if not arduino[0]:
            return jsonify(error="Arduino já existente"), 409

        return jsonify(message="Sala criada com sucesso"), 200
    except Exception:
        return jsonify(error="Ocorreu um problema ao inserir na base de dados."), 500


@admin.route("/admin/salas/eliminar/<int:sala_id>", methods=["DELETE"])
def admin_salas_eliminar(sala_id):
    try:
        sala = Sala.delete(sala_id)
        if not sala:
            return jsonify(error="Sala não encontrada"), 404

        arduino = Arduino.delete(Arduino.get_arduino_by_sala("id", sala_id).id)
        if not arduino:
            return jsonify(error="Arduino não encontrado"), 404

        return jsonify(), 200
    except Exception:
        return jsonify(error="Ocorreu um problema ao eliminar da base de dados."), 500


@admin.route("/admin/aulas/<string:tipo>", methods=["GET"])
def admin_aulas(tipo):
    match tipo:
        case "todas":
            # Todas as aulas
            return jsonify(aulas=[{
                "id": aula.id,
                "unidade": aula.unidade.nome,
                "sala": aula.sala.nome,
                "turma": aula.turma.nome,
                "data": aula.created_at.strftime("%d/%m/%Y %H:%M"),
            } for aula in Aula.query.all()]), 200

        case "ativas":
            # Aulas ativas
            from main import aulas_a_decorrer
            return jsonify(aulas=[{
                "sala": sala,
                "estado": dados["estado"],
                "inicio": dados["inicio"].strftime("%d/%m/%Y %H:%M"),
                "unidade": Unidade.query.get(dados["unidade_id"]).nome,
                "turma": Turma.query.get(dados["turma_id"]).nome,
            } for sala, dados in aulas_a_decorrer.items()]), 200

        case _:
            return jsonify(error="Tipo de aula inválido"), 400


@admin.route("/admin/aulas/<string:tipo>/<string:aula>", methods=["GET"])
def admin_aulas_detalhes(tipo, aula):
    match tipo:
        case "todas":
            # Todas as aulas
            aula = Aula.query.filter_by(id=aula).first()
            if not aula:
                return jsonify(error="Aula não encontrada"), 404

            return jsonify(aula={
                "id": aula.id,
                "unidade": {
                    "codigo": aula.unidade.codigo,
                    "nome": aula.unidade.nome
                },
                "sala": aula.sala.nome,
                "professor": f"p{aula.professor.id}",
                "turma": aula.turma.nome,
                "data": aula.created_at.strftime("%d/%m/%Y %H:%M"),
                "presencas": [{
                    "aluno": presenca.aluno.id,
                    "presenca": presenca.created_at.strftime("%d/%m/%Y %H:%M")
                } for presenca in aula.presencas],
            }), 200

        case "ativas":
            # Aulas ativas
            from main import aulas_a_decorrer
            dados = aulas_a_decorrer.get(aula)

            if not dados:
                return jsonify(error="Aula não encontrada"), 404

            unidade = Unidade.query.get(dados["unidade_id"])
            return jsonify(aula={
                "sala": aula,
                "estado": dados["estado"],
                "inicio": dados["inicio"].strftime("%d/%m/%Y %H:%M"),
                "unidade": {
                    "codigo": unidade.codigo,
                    "nome": unidade.nome
                },
                "professor": f"p{Professor.query.get(dados['professor_id']).id}",
                "turma": Turma.query.get(dados["turma_id"]).nome,
                "presencas": [{
                    "aluno": presenca["numero"],
                    "presenca": presenca["timestamp"].strftime("%d/%m/%Y %H:%M")
                } for presenca in dados["alunos"]],
            }), 200

        case _:
            return jsonify(error="Tipo de aula inválido"), 400
