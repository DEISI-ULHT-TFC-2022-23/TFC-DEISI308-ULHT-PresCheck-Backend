from flask import Blueprint, request, render_template, redirect, url_for, flash
from werkzeug.security import check_password_hash
from flask_login import login_user, login_required, logout_user
from models import User

auth = Blueprint('auth', __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        # Obtém o usuário com base no nome de usuário fornecido
        user = User.query.filter_by(username=username).first()

        # Verifica se o usuário existe e se a senha fornecida está correta
        if not user or not check_password_hash(user.password, password):
            flash('Verifique os seus dados e tente novamente.', 'error')
            # Redireciona de volta para a página de login em caso de erro
            return redirect(url_for('auth.login'))

        # Verifica se o usuário está ativo
        if not user.is_active():
            flash('O seu utilizador está desativado. Contate a Direção do DEISI.', 'error')
            # Redireciona de volta para a página de login em caso de usuário desativado
            return redirect(url_for('auth.login'))

        # Efetua o login do usuário
        login_user(user, remember=remember)
        # Redireciona para a página inicial após o login bem-sucedido
        return redirect(url_for('main.index'))

    # Renderiza a página de login se o método da requisição for GET
    render_template("login.html")


@auth.route('/logout')
@login_required
def logout():
    # Efetua o logout do usuário atualmente logado
    logout_user()
    # Redireciona para a página de login após o logout
    return redirect(url_for('auth.login'))

