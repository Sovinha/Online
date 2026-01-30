from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
from app.extensions import db
from app.models import Historico

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXPORT_DIR = os.path.join(BASE_DIR, "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

def gerar_pdf(historico_id):
    # Substituindo o .query.get pelo .session.get
    h = db.session.get(Historico, historico_id)
    
    if not h:
        return None

    path = os.path.join(
        EXPORT_DIR,
        f"pagamento_{h.loja.replace(' ', '_')}_{h.id}.pdf"
    )

    c = canvas.Canvas(path, pagesize=A4)
    y = 800

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"RELATÓRIO DE PAGAMENTO - {h.loja.upper()}")
    y -= 25
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Data: {h.data.strftime('%d/%m/%Y %H:%M')}")
    c.drawString(250, y, f"Turno: {h.turno}")
    y -= 30
    
    c.line(50, y+10, 550, y+10)

    for m in h.motoboys:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, f"Motoboy: {m.motoboy}")
        y -= 15
        c.setFont("Helvetica", 10)
        c.drawString(70, y, f"Entregas: {m.entregas} | Final: R$ {m.valor_final:.2f}")
        
        if m.motivo_ajuste:
            y -= 12
            c.setFont("Helvetica-Oblique", 9)
            c.drawString(70, y, f"Ajuste: R$ {m.ajuste:.2f} - Motivo: {m.motivo_ajuste}")
        
        y -= 20 

        # Controle de quebra de página
        if y < 100:
            c.showPage()
            y = 800

    y -= 20
    c.line(50, y+15, 550, y+15)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"TOTAL GERAL PAGO: R$ {h.total:.2f}")
    c.save()

    return path