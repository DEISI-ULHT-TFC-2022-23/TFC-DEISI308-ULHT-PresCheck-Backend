from flask import Blueprint, jsonify
from werkzeug.security import generate_password_hash
from models import *

admin = Blueprint('admin', __name__)

demo_username = "demo"
demo_password = "demo"


@admin.route("/admin/demo/criar", methods=["GET"])
def admin_demo_criar():
    db.drop_all()
    db.create_all()
    user = User(username=demo_username, password=generate_password_hash(demo_password, method='sha256'))
    db.session.add(user)
    db.session.commit()
    get_user = User.query.filter_by(username=user.username).first()
    return jsonify(id=get_user.id, username=get_user.username, password="password",
                   is_admin=get_user.e_admin, is_active=get_user.esta_ativo,
                   created_at=get_user.criado_em), 200


@admin.route("/admin/prof/criar", methods=["GET"])
def admin_prof_criar():
    db.drop_all()
    db.create_all()
    professor = Professor(1)
    unidade1 = Unidade(15151, "Matemática")
    unidade2 = Unidade(1048294, "Segurança Informática")
    professor.user = 1
    professor.unidades.append(unidade1)
    professor.unidades.append(unidade2)
    db.session.add(professor)
    db.session.add_all([unidade1, unidade2])
    db.session.commit()
    get_prof = Professor.query.get(1)
    return jsonify(id=get_prof.id, unidades=[{'unidade_id': unidade.id, 'unidade_nome': unidade.nome} for unidade in professor.unidades]), 200
