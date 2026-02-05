import os
import sys
import importlib.util

# 1. Forçar o caminho da pasta raiz
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

# 2. MÉTODO INFALÍVEL: Importar o __init__.py diretamente pelo caminho do arquivo
init_path = os.path.join(BASE_DIR, "app", "__init__.py")
spec = importlib.util.spec_from_file_location("app", init_path)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
create_app = app_module.create_app

# 3. Importar os outros módulos necessários
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

def criar():
    app = create_app()
    with app.app_context():
        print("🔨 Conectando ao banco...")
        db.create_all()
        
        user = User.query.filter_by(username="admin").first()
        if not user:
            print("👤 Criando conta do administrador...")
            senha_hash = generate_password_hash("admin123")
            user = User(username="admin", password=senha_hash)
            db.session.add(user)
            db.session.commit()
            print("✅ SUCESSO: Usuário 'admin' criado!")
        else:
            user.password = generate_password_hash("admin123")
            db.session.commit()
            print("ℹ️ O admin já existe. Senha atualizada para 'admin123'.")

if __name__ == "__main__":
    criar()