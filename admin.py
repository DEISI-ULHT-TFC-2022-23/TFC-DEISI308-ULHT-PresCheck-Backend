from flask import Blueprint, jsonify
from werkzeug.security import generate_password_hash
from models import *

admin = Blueprint('admin', __name__)


@admin.route("/admin", methods=["GET"])
def admin_index():
    db.drop_all()
    db.create_all()
    user = User(username="user", password=generate_password_hash("password"))
    user.is_admin = True
    user.is_active = True
    db.session.add(user)
    db.session.commit()
    select_user = User.query.filter_by(username="user").first()
    return jsonify(id=select_user.id, username=select_user.username, password="password",
                   is_admin=select_user.is_admin, is_active=select_user.is_active,
                   created_at=select_user.created_at), 200
