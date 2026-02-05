import os
from flask import Flask
from app.extensions import db, login_manager

def create_app():
    app = Flask(__name__)
    
    # PEGA A URL DO RENDER (SUPABASE), SE NÃO ACHAR, USA O LOCAL (SEGURANÇA)
    database_url = os.environ.get('DATABASE_URL')
    
    # CORREÇÃO PARA O SQLALCHEMY (Ele exige 'postgresql://' e o Render às vezes manda 'postgres://')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'uma-chave-muito-segura'

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from app.routes import bp
        app.register_blueprint(bp)
        # CRIA AS TABELAS NO SUPABASE AUTOMATICAMENTE SE NÃO EXISTIREM
        db.create_all()

    return app