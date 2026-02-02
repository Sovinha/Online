from app.app import create_app
from app.extensions import db
from sqlalchemy import text # Importação necessária para rodar o comando SQL

app = create_app()

# Este bloco verifica e cria as novas colunas e tabelas automaticamente
with app.app_context():
    # 1. Cria tabelas novas (se houver)
    db.create_all()
    
    # 2. Adiciona as colunas novas manualmente caso elas ainda não existam
    try:
        # Adiciona coluna 'pedidos' na tabela historico_motoboy
        db.session.execute(text("ALTER TABLE historico_motoboy ADD COLUMN IF NOT EXISTS pedidos TEXT"))
        # Adiciona coluna 'motivo_ajuste' na tabela historico_motoboy
        db.session.execute(text("ALTER TABLE historico_motoboy ADD COLUMN IF NOT EXISTS motivo_ajuste VARCHAR(255)"))
        
        db.session.commit()
        print("✅ Colunas de histórico atualizadas com sucesso!")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Nota: As colunas podem já existir ou houve um erro menor: {e}")

if __name__ == "__main__":
    # O host 0.0.0.0 é necessário para que o Render consiga acessar a aplicação
    app.run(host="0.0.0.0", port=10000, debug=False)