import os
from flask import Flask
from app.extensions import db, login_manager

def create_app():
    app = Flask(__name__)
    
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # CORREÇÃO PARA PORTA 6543 (Modo Transaction do Supabase)
        # O modo pooler exige prepared_statement=false para evitar erros de cache de plano
        if ":6543" in database_url:
            if "?" in database_url:
                if "prepared_statement=false" not in database_url:
                    database_url += "&prepared_statement=false"
            else:
                database_url += "?prepared_statement=false"

        # Remove o parâmetro pgbouncer antigo se ele ainda existir
        database_url = database_url.replace("?pgbouncer=true", "")
            
        # SQLAlchemy exige 'postgresql://' (o Render/Supabase às vezes envia 'postgres://')
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave-de-seguranca-padrao')

    # Configurações de Pool otimizadas para o Supabase
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,  # Verifica se a conexão está viva antes de usar
        "pool_recycle": 300,    # Recicla conexões a cada 5 minutos
    }

    # Inicializa as extensões
    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        # Importa e registra as rotas
        from app.routes import bp
        app.register_blueprint(bp)
        
        # Tenta criar as tabelas (db.create_all)
        try:
            db.create_all()
            print("Conexão com Supabase (Porta 6543) estabelecida com sucesso!")
        except Exception as e:
            print(f"Erro ao sincronizar tabelas no Supabase: {e}")

    return app