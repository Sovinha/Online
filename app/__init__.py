from flask import Flask
from app.extensions import db, login_manager
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'chave-estoque-99'
    
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'banco.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    
    login_manager.login_view = 'main.login'

    with app.app_context():
        from app.routes import bp as main_bp
        app.register_blueprint(main_bp)
        
        # ESSAS LINHAS RESOLVEM O ERRO DE LINKS NO BASE.HTML
        app.add_url_rule('/login', endpoint='auth.login', build_only=True)
        app.add_url_rule('/logout', endpoint='auth.logout', build_only=True)

    return app