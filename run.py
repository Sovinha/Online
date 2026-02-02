import os
from sqlalchemy import text
from app.app import create_app
from app.extensions import db

app = create_app()

# Este bloco gerencia a persistência no Supabase e atualizações de colunas
with app.app_context():
    # 1. Cria tabelas no novo banco (Supabase)
    db.create_all()
    
    # 2. Lógica de atualização de colunas
    # Nota: O PostgreSQL não suporta "IF NOT EXISTS" direto no ALTER TABLE em versões antigas,
    # por isso usamos um bloco try/except robusto.
    try:
        # Verifica se estamos no SQLite ou PostgreSQL para usar a sintaxe correta
        is_postgres = "postgresql" in str(db.engine.url)
        
        # Comando para adicionar coluna 'pedidos'
        try:
            db.session.execute(text("ALTER TABLE historico_motoboy ADD COLUMN pedidos TEXT"))
            db.session.commit()
        except:
            db.session.rollback()

        # Comando para adicionar coluna 'motivo_ajuste'
        try:
            db.session.execute(text("ALTER TABLE historico_motoboy ADD COLUMN motivo_ajuste VARCHAR(255)"))
            db.session.commit()
        except:
            db.session.rollback()
            
        print("✅ Verificação de colunas concluída no banco persistente!")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Nota: Colunas já existentes ou erro de migração: {e}")

if __name__ == "__main__":
    # O Render define a porta automaticamente, se não houver, usa a 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
