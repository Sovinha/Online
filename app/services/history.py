import os
from app.extensions import db  # Importação necessária para o session.get
from app.models import Historico

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXPORT_DIR = os.path.join(BASE_DIR, "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

def gerar_txt(historico_id):
    # Forma moderna de buscar por ID
    h = db.session.get(Historico, historico_id)
    
    if not h:
        return None

    path = os.path.join(
        EXPORT_DIR,
        f"pagamento_{h.loja.replace(' ', '_')}_{h.id}.txt"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"--- FECHAMENTO DE ENTREGAS ---\n")
        f.write(f"Loja: {h.loja.upper()}\n")
        f.write(f"Turno: {h.turno}\n")
        f.write(f"Data: {h.data.strftime('%d/%m/%Y %H:%M')}\n")
        f.write(f"------------------------------\n\n")

        for m in h.motoboys:
            f.write(f"Motoboy: {m.motoboy}\n")
            f.write(f"   Entregas: {m.entregas}\n")
            f.write(f"   VALOR FINAL: R$ {m.valor_final:.2f}\n")
            if m.motivo_ajuste:
                f.write(f"   Ajuste: R$ {m.ajuste:.2f} ({m.motivo_ajuste})\n")
            f.write("-" * 20 + "\n")

        f.write(f"\nTOTAL GERAL: R$ {h.total:.2f}\n")

    return path