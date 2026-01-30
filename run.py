from app.app import create_app
from app.extensions import db

app = create_app()

# Este bloco verifica e cria as novas colunas (faturamento, taxas, etc.) 
# automaticamente sempre que o site iniciar no Render.
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    # O host 0.0.0.0 é necessário para que o Render consiga acessar a aplicação
    app.run(host="0.0.0.0", port=10000, debug=False)