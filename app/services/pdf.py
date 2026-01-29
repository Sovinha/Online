from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
from app.models import Historico

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXPORT_DIR = os.path.join(BASE_DIR, "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

def gerar_pdf(historico_id):
    h = Historico.query.get(historico_id)

    path = os.path.join(
        EXPORT_DIR,
        f"pagamento_{h.loja}_{h.id}.pdf"
    )

    c = canvas.Canvas(path, pagesize=A4)
    y = 800

    c.drawString(50, y, f"Loja: {h.loja}")
    y -= 20
    c.drawString(50, y, f"Data: {h.data.strftime('%d/%m/%Y %H:%M')}")
    y -= 30

    for m in h.motoboys:
        c.drawString(50, y, f"Motoboy: {m.motoboy}")
        y -= 15
        c.drawString(70, y, f"Original: R$ {m.valor_original:.2f}")
        y -= 15
        c.drawString(70, y, f"Ajuste: R$ {m.ajuste:.2f}")
        y -= 15
        c.drawString(70, y, f"Final: R$ {m.valor_final:.2f}")
        y -= 15
        if m.motivo_ajuste:
            c.drawString(70, y, f"Motivo: {m.motivo_ajuste}")
            y -= 15
        y -= 10

        if y < 100:
            c.showPage()
            y = 800

    c.drawString(50, y, f"TOTAL GERAL: R$ {h.total:.2f}")
    c.save()

    return path
