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

    # CONFIGURAÇÕES OTIMIZADAS PARA VELOCIDADE (POOL DE CONEXÕES)
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_size": 10,                # Mantém 10 conexões sempre abertas
        "max_overflow": 20,             # Abre até +20 em picos de acesso
        "pool_timeout": 30,             # Tempo de espera por conexão
        "pool_recycle": 1800,           # Recicla conexões a cada 30 min (evita idle timeout)
        "pool_pre_ping": True,          # Verifica se a conexão caiu antes de usá-la
        "connect_args": connect_args
    }

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from app.routes import bp
        app.register_blueprint(bp)
        
        try:
            db.create_all()
            
            from app.models import User
            from werkzeug.security import generate_password_hash
            
            usuarios_reset = [
                {'u': 'admin', 'p': 'admin123'},
                {'u': 'galca', 'p': 'galca'}
            ]

            for user_data in usuarios_reset:
                user_obj = User.query.filter_by(username=user_data['u']).first()
                
                if user_obj and not user_obj.password.startswith(('scrypt', 'pbkdf2')):
                    db.session.delete(user_obj)
                    db.session.commit()
                    user_obj = None
                
                if not user_obj:
                    novo_user = User(
                        username=user_data['u'],
                        password=generate_password_hash(user_data['p'])
                    )
                    db.session.add(novo_user)
                    db.session.commit()
                    print(f">>> Usuário '{user_data['u']}' resetado com senha criptografada.")
                
            print("Conexão estável e otimizada com Supabase estabelecida.")
        except Exception as e:
            print(f"Erro ao configurar usuários: {e}")

    return app