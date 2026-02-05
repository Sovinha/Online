from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.extensions import db
from werkzeug.security import check_password_hash # Importante para segurança

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Se o usuário já estiver logado, manda direto para o dashboard
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Busca o usuário pelo username
        user = User.query.filter_by(username=username).first()

        # SEGURANÇA: Usar check_password_hash em vez de comparação direta (==)
        # Isso assume que você salvou a senha usando generate_password_hash
        if user and check_password_hash(user.password, password):
            login_user(user)
            # Redireciona para o dashboard, que é a tela principal pós-login
            return redirect(url_for("main.dashboard"))
        
        # Caso falhe (usuário não existe ou senha errada)
        flash("Usuário ou senha inválidos", "danger")
        return redirect(url_for("auth.login"))

    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sessão encerrada com sucesso.", "info")
    return redirect(url_for("auth.login"))