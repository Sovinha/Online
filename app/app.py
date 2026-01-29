from flask import Flask
from app.extensions import db, login_manager
from app.routes import bp
from app.auth import auth_bp
from app.models import User

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "chave-secreta-desenvolvimento"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()

    return app
