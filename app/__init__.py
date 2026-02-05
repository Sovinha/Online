import os
from flask import Flask
from app.extensions import db, login_manager

def create_app():
    app = Flask(__name__)
    
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Remove pgbouncer que causa erro no psycopg2
        if "?pgbouncer=true" in database_url:
            database_url = database_url.replace("?pgbouncer=true", "")
            
        # SQLAlchemy exige 'postgresql://'
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave-de-seguranca-padrao')

    # Pool estável para Supabase
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from app.routes import bp
        app.register_blueprint(bp)
        
        try:
            db.create_all()
            print("Banco de dados sincronizado com Supabase.")
        except Exception as e:
            print(f"Erro ao conectar no banco: {e}")

    return app