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
    sala = request.json["sala"]
    user = User.create(username, password, is_admin, True)
    user[1].associate_prof(professor_id, commit=True)
    sala = Sala.create(sala, "123")
    return jsonify(username=user[1].username, password=password, is_admin=user[1].is_admin,
                   professor_id=professor_id, unidades=Professor.get_unidades(professor_id),
                   sala=sala[1].nome), 200

@admin.route("/admin/utilizadores/editar/<int:id>", methods=["POST"])
def admin_utilizadores_editar(id):
    # edita um utilizador específico
    username = request.json["username"]
    password = request.json["password"]
    is_admin = request.json["is_admin"]
    professor_id = request.json["professor_id"]
    unidades = request.json["unidades"]
    sala = request.json["sala"]
    user = User.query.filter(User.id == id).first()
    user.username = username
    user.password = password
    user.is_admin = is_admin
    user.professor_id = professor_id
    user.unidades = unidades
    user.sala = sala
    db.session.commit()
    return jsonify(username=user.username, password=user.password, is_admin=user.is_admin,
                   professor_id=user.professor_id, unidades=Professor.get_unidades(user.professor_id),
                   sala=user.sala.nome), 200
