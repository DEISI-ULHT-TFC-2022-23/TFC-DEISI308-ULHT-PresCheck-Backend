from crypt import methods

from flask import Blueprint, jsonify, request
from models import *

admin = Blueprint('admin', __name__)

demo_username = "demo"
demo_password = "demo"


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
    # retora todos os alunos
    return jsonify(alunos=Aluno.query.all()), 200
@admin.route("/admin/alunos/criar", methods=["PUT"])
def admin_alunos_criar():
    # cria um aluno
    aluno_id = request.json["id"]
    Aluno.create(aluno_id)
    return 200
@admin.route("/admin/alunos/<int:id>", methods=["GET"])
def admin_alunos_id(id):
    # retorna um aluno específico
    return jsonify(aluno=Aluno.query.filter_by(aluno_id = id).first()), 200

# @admin.route("/admin/aluno/editar/<int:id>", methods=["POST"])
# def admin_alunos_editar(id):
#     dispositivos = request.json["dispositivos"]
#     dispostivos_bs = Dispositivo.query.filter_by(aluno_id = id).all()
#
#     db.session.commit()
#     return jsonify(aluno_id=aluno.aluno_id), 200

@admin.route("/admin/salas", methods=["GET"])
def admin_salas():
    return jsonify(salas=Sala.query.all()), 200

@admin.route("/admin/salas/criar", methods=["PUT"])
def admin_salas_criar():
    # cria uma sala
    sala_nome = request.json["nome"]
    sala_arduino = request.json["arduino"]
    Sala.create(sala_nome, sala_arduino)
    return 200
@admin.route("/admin/salas/editar/<int:id>", methods=["POST"])
def admin_salas_editar(id):
    sala_nome = request.json["nome"]
    sala = Sala.get(id)
    sala.nome = sala_nome
    db.session.commit()
    return 200
@admin.route("/admin/salas/eliminar/<int:id>", methods=["DELETE"])
def admin_salas_eliminar():
    # apaga uma sala específico
    Sala.query.filter(Sala.id == id).delete()
    db.session.commit()
    return "", 200
@admin.route("/admin/aulas", methods=["GET"])
def admin_aulas():
    # retora todos as aulas
    return jsonify(aulas=Aula.query.all()), 200
@admin.route("/admin/aulas/<int:id>", methods=["GET"])
def admin_aulas_id(id):
    # retorna um aluno específico
    return jsonify(aula=Aula.query.filter_by(id = id).first()), 200

@admin.route("/admin/aula/eliminar/<int:id>", methods=["DELETE"])
def admin_aula_eliminar():
    # apaga uma aula específico
    Aula.query.filter(Aula.id == id).delete()
    db.session.commit()
    return "", 200

@admin.route("/admin/unidades", methods=["GET"])
def admin_unidades():
    # retorna todas as unidades
    return jsonify(unidades=Unidade.query.all()), 200

@admin.route("/admin/unidades/<int:id>", methods=["GET"])
def admin_unidades_id(id):
    # retorna uma unidade específico
    return jsonify(unidade=Unidade.get(id)), 200
@admin.route("/admin/unidades/criar", methods=["PUT"])
def admin_unidades_criar():
    # cria uma uniddade
    unidades_id = request.json["id"]
    unidades_nome = request.json["nome"]
    Unidade.create(unidades_id, unidades_nome)
    return 200
@admin.route("/admin/unidades/editar/<int:id>", methods=["POST"])
def admin_unidades_editar(id):
    # edita uma unidade em específico
    unidades_nome = request.json["nome"]
    unidade = Unidade.get(id)
    unidade.nome = unidades_nome
    db.session.commit()
    return 200
@admin.route("/admin/unidades/eliminar/<int:id>", methods=["DELETE"])
def admin_unidades_eliminar():
    # apaga uma unidade específico
    Unidade.query.filter(Unidade.id == id).delete()
    db.session.commit()
    return "", 200