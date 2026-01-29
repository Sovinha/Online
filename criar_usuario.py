from app.app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    if not User.query.filter_by(username="admin").first():
        user = User(username="admin", password="admin123")
        db.session.add(user)
        db.session.commit()
        print("Usuário criado com sucesso!")
    else:
        print("Usuário já existe.")
