import os
from app.models import Historico

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXPORT_DIR = os.path.join(BASE_DIR, "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

def gerar_txt(historico_id):
    h = Historico.query.get(historico_id)

    path = os.path.join(
        EXPORT_DIR,
        f"pagamento_{h.loja}_{h.id}.txt"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Loja: {h.loja}\n")
        f.write(f"Data: {h.data.strftime('%d/%m/%Y %H:%M')}\n\n")

        for m in h.motoboys:
            f.write(f"Motoboy: {m.motoboy}\n")
            f.write(f"  Valor original: R$ {m.valor_original:.2f}\n")
            f.write(f"  Ajuste: R$ {m.ajuste:.2f}\n")
            f.write(f"  Valor final: R$ {m.valor_final:.2f}\n")
            if m.motivo_ajuste:
                f.write(f"  Motivo: {m.motivo_ajuste}\n")
            f.write("\n")

        f.write(f"TOTAL GERAL: R$ {h.total:.2f}\n")

    return path
