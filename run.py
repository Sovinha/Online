import os
import sys

# Garante que a pasta 'app' seja encontrada
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    # Apenas garante que o admin exista
    try:
        from werkzeug.security import generate_password_hash
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            db.session.add(User(username="admin", password=generate_password_hash("admin123")))
            db.session.commit()
            print("👤 Usuário admin verificado/criado.")
    except Exception as e:
        print(f"Nota: Admin já existente ou erro leve: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🚀 Saturnino Online pronto: http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)