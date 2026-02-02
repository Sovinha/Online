import os # Importação necessária para ler as variáveis do Render
from flask import Flask
from app.extensions import db, login_manager
from app.routes import bp
from app.auth import auth_bp
from app.models import User

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "chave-secreta-desenvolvimento"
    
    # --- CONFIGURAÇÃO DE BANCO DE DADOS DINÂMICA ---
    # Tenta ler a URL do Supabase configurada no Render
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Correção crucial: SQLAlchemy exige 'postgresql://' e o Render pode enviar 'postgres://'
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    else:
        # Se estiver rodando no seu PC localmente, continua usando SQLite
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    # -----------------------------------------------

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(bp)

    # Nota: db.create_all() agora criará as tabelas no Supabase automaticamente no primeiro acesso
    with app.app_context():
        db.create_all()

    return app
