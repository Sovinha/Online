import os
from flask import Flask
from app.extensions import db, login_manager

def create_app():
    app = Flask(__name__)
    
    database_url = os.environ.get('DATABASE_URL')
    connect_args = {}

    if database_url:
        # Limpa a URL de parâmetros que o psycopg2 não entende
        if "prepared_statement=" in database_url:
            # Remove o parâmetro da string para não dar erro de DSN inválida
            import urllib.parse as urlparse
            url_parts = list(urlparse.urlparse(database_url))
            query = dict(urlparse.parse_qsl(url_parts[4]))
            query.pop('prepared_statement', None)
            url_parts[4] = urlparse.urlencode(query)
            database_url = urlparse.urlunparse(url_parts)

        # Se for Supabase porta 6543, injetamos a configuração via connect_args
        if ":6543" in database_url:
            connect_args["options"] = "-c prepared_statements=off"

        # Correção padrão de protocolo
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave-de-seguranca-padrao')

    # Aplicando as correções no Engine
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": connect_args  # <--- Aqui entra a correção do erro
    }

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from app.routes import bp
        app.register_blueprint(bp)
        
        try:
            db.create_all()
            print("Conexão estável com Supabase estabelecida.")
        except Exception as e:
            print(f"Nota: {e}")

    return app