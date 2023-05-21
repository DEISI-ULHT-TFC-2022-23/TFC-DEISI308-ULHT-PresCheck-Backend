from flask import Blueprint, jsonify
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
