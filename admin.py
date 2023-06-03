from flask import Blueprint, jsonify, request
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
    return jsonify(utilizadores=User.query.filter(User.id != 1).all()), 200


@admin.route("/admin/utilizadores/<int:id>", methods=["GET"])
def admin_utilizadores_id(id):
    # retorna um utilizador específico
    return jsonify(utilizador=User.query.filter(User.id == id).first()), 200


@admin.route("/admin/utilizadores/apagar/<int:id>", methods=["DELETE"])
def admin_utilizadores_delete(id):
    # deleta um utilizador específico
    User.query.filter(User.id == id).delete()
    db.session.commit()
    return "", 200


@admin.route("/admin/utilizadores/criar", methods=["PUT"])
def admin_utilizadores_criar():
    # cria um utilizador
    username = request.json["username"]
    password = request.json["password"]
    is_admin = request.json["is_admin"]
    professor_id = request.json["professor_id"]
    unidades = request.json["unidades"]
    user = User.create(username, password, is_admin, True)
    user[1].associate_prof(professor_id, commit=True)
    return jsonify(username=user[1].username, password=password, is_admin=user[1].is_admin,
                   professor_id=professor_id, unidades=Professor.get_unidades(professor_id)), 200


@admin.route("/admin/utilizadores/editar/<int:id>", methods=["POST"])
def admin_utilizadores_editar(id):
    # edita um utilizador específico
    username = request.json["username"]
    password = request.json["password"]
    is_admin = request.json["is_admin"]
    professor_id = request.json["professor_id"]
    unidades = request.json["unidades"]
    user = User.query.filter(User.id == id).first()
    user.username = username
    user.password = password
    user.is_admin = is_admin
    user.professor_id = professor_id
    user.unidades = unidades
    db.session.commit()
    return jsonify(username=user.username, password=user.password, is_admin=user.is_admin,
                   professor_id=user.professor_id, unidades=Professor.get_unidades(user.professor_id)), 200


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


@admin.route("/admin/alunos/criar", methods=["PUT"])
def admin_alunos_criar():
    params = request.get_json()
    numero, dispositivo = params["numero"], params["dispositivo"]
    if not numero:
        return jsonify(error="[CRITICAL] Falta parâmetros para completar o processo!"), 400

    try:
        numero = int(numero)
        aluno = Aluno.create(numero)

        if dispositivo is not None:
            Dispositivo.create(dispositivo, aluno[1].id)

        return jsonify(), 200
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
