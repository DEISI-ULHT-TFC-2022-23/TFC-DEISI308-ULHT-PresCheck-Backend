from flask import Blueprint, jsonify
from models import *

admin = Blueprint('admin', __name__)

demo_username = "demo"
demo_password = "demo"


@admin.route("/admin/demo/criar", methods=["GET"])
def admin_demo_criar():
    user = User.create(demo_username, demo_password, True, True)
    return jsonify(username=user.username, password=demo_password, is_admin=user.is_admin), 200


@admin.route("/admin/prof/criar", methods=["GET"])
def admin_prof_criar():
    unidades = [Unidade.create(15151, "Matemática"), Unidade.create(1048294, "Segurança Informática")]
    professor = Professor.create(1, unidades)
    user = User.query.get(1)
    user.associate_prof(1, commit=True)
    return jsonify(id=professor.id, unidades=Professor.get_unidades(professor.id)), 200


@admin.route("/admin/sala/criar", methods=["GET"])
def admin_sala_criar():
    sala = Sala.create("F.2.3", "123")
    return jsonify(id=sala.nome), 200
