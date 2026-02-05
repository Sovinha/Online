from app import db, create_app
from app.models import User, Historico
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    db.drop_all() # Limpa tudo
    db.create_all() # Cria do zero com a coluna ERROS e a tabela USER

    # Cria o seu acesso
    admin = User(username='admin', password=generate_password_hash('123'))
    db.session.add(admin)
    db.session.commit()
    print("Banco de dados resetado e pronto!")