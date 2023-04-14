from flask import Blueprint, request, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from models import *

admin = Blueprint('admin', __name__)


@admin.route("/admin")
@login_required
def admin_index():
    return "Página Inicial ADMIN"
