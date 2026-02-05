import os
from flask import Flask
from app.extensions import db, login_manager
from app.routes import bp
from app.auth import auth_bp
from app.models import User

def create_app():
    app = Flask(__name__)

    # 1. Configurações de Segurança e Sessão
    # Importante: Se estiver no Render, defina a variável SECRET_KEY no painel
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "chave-secreta-padrao-123")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Previne que o navegador recuse o cookie de login em conexões HTTP (comum em dev)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = False  # Mude para True apenas se usar HTTPS/SSL
    app.config["REMEMBER_COOKIE_DURATION"] = 3600 # 1 hora de sessão

    # 2. Configuração de Banco de Dados (Supabase ou SQLite)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"

    # 3. Inicialização das Extensões
    db.init_app(app)
    login_manager.init_app(app)
    
    # Define a rota de login (O nome aqui deve ser 'auth.login' porque o blueprint é auth_bp)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    # 4. Carregador de Usuário (Obrigatório para o Flask-Login)
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # 5. Registro de Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(bp)

    # 6. Criação das Tabelas
    with app.app_context():
        db.create_all()

    return app