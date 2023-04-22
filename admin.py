from flask import Blueprint, jsonify
from werkzeug.security import generate_password_hash
from models import *

admin = Blueprint('admin', __name__)

demo_username = "demo"
demo_password = "demo"


@admin.route("/admin/demo/criar", methods=["GET"])
def admin_demo_criar():
    user = User(username=demo_username, password=generate_password_hash(demo_password, method='sha256'))
    user.is_active = True
    user.is_admin = True
    db.session.add(user)
    db.session.commit()
    get_user = User.query.filter_by(username=user.username).first()
    return jsonify(username=get_user.username, password=demo_password, is_admin=get_user.is_admin), 200


@admin.route("/admin/prof/criar", methods=["GET"])
def admin_prof_criar():
    professor = Professor(1)
    unidade1 = Unidade(15151, "Matemática")
    unidade2 = Unidade(1048294, "Segurança Informática")
    user = User.query.get(1)
    user.professor_id = 1
    professor.unidades.append(unidade1)
    professor.unidades.append(unidade2)
    db.session.add(professor)
    db.session.add(user)
    db.session.add_all([unidade1, unidade2])
    db.session.commit()
    get_prof = Professor.query.get(1)
    return jsonify(id=get_prof.id, unidades=professor.get_unidades()), 200


@admin.route("/admin/sala/criar", methods=["GET"])
def admin_sala_criar():
    sala = Sala("F.2.3", generate_password_hash("123", method="sha256"))
    db.session.add(sala)
    db.session.commit()
    return jsonify(id=sala.nome), 200
