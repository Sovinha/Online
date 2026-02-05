import os
import sys
from sqlalchemy import text

# Garante que a pasta 'app' seja encontrada
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    # 1. Cria o banco e as tabelas
    db.create_all()
    
    # 2. Garante as colunas novas no SQLite/Postgres
    try:
        db.session.execute(text("ALTER TABLE historico_motoboy ADD COLUMN pedidos TEXT"))
        db.session.commit()
    except:
        db.session.rollback()

    try:
        db.session.execute(text("ALTER TABLE historico_motoboy ADD COLUMN motivo_ajuste VARCHAR(255)"))
        db.session.commit()
    except:
        db.session.rollback()

    # 3. CRIA O USUÁRIO ADMIN AUTOMATICAMENTE
    from app.models import User
    from werkzeug.security import generate_password_hash
    
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        hashed_pw = generate_password_hash("admin123")
        db.session.add(User(username="admin", password=hashed_pw))
        db.session.commit()
        print("✅ Usuário 'admin' criado! Senha: admin123")
    else:
        print("ℹ️ Usuário admin já verificado.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Servidor rodando em: http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)