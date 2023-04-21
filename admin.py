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
                   created_at=get_user.created_at), 200
