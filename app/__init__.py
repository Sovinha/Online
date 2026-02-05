import os
from flask import Flask
from app.extensions import db, login_manager

def create_app():
    app = Flask(__name__)
    
    database_url = os.environ.get('DATABASE_URL')
    connect_args = {}

    if database_url:
        if "prepared_statement=" in database_url:
            import urllib.parse as urlparse
            url_parts = list(urlparse.urlparse(database_url))
            query = dict(urlparse.parse_qsl(url_parts[4]))
            query.pop('prepared_statement', None)
            url_parts[4] = urlparse.urlencode(query)
            database_url = urlparse.urlunparse(url_parts)

        if ":6543" in database_url:
            connect_args["options"] = "-c prepared_statements=off"

        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'chave-de-seguranca-padrao')

    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": connect_args
    }

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from app.routes import bp
        app.register_blueprint(bp)
        
        try:
            db.create_all()
            
            # SCRIPT DE CRIAÇÃO DE USUÁRIO INICIAL
            from app.models import User
            from werkzeug.security import generate_password_hash
            
            if not User.query.filter_by(username='admin').first():
                admin_user = User(
                    username='admin',
                    password=generate_password_hash('admin123')
                )
                db.session.add(admin_user)
                db.session.commit()
                print(">>> Usuário 'admin' criado com senha 'admin123'")
                
            print("Conexão estável com Supabase estabelecida.")
        except Exception as e:
            print(f"Nota/Erro no banco: {e}")

    return app