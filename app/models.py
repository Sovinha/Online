from datetime import datetime
import pytz
from flask_login import UserMixin
from app.extensions import db

# Função auxiliar para garantir o horário de Brasília em todo o banco de dados
def get_br_time():
    return datetime.now(pytz.timezone('America/Sao_Paulo'))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Historico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Usamos default=get_br_time para a data de criação ser automática e correta
    data = db.Column(db.DateTime, default=get_br_time)
    loja = db.Column(db.String(50), index=True)
    turno = db.Column(db.String(20), index=True) 
    total = db.Column(db.Float, default=0.0)
    
    # NOVOS CAMPOS FINANCEIROS PARA O PATRÃO
    faturamento_pedidos = db.Column(db.Float, default=0.0)
    taxas_clientes = db.Column(db.Float, default=0.0)
    
    arquivo_txt = db.Column(db.String(255))
    arquivo_pdf = db.Column(db.String(255))

    motoboys = db.relationship("HistoricoMotoboy", backref="historico", cascade="all, delete-orphan")

class HistoricoMotoboy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    historico_id = db.Column(db.Integer, db.ForeignKey("historico.id"), nullable=False, index=True)
    data = db.Column(db.DateTime, default=get_br_time)
    loja = db.Column(db.String(50), index=True)
    turno = db.Column(db.String(20), index=True) 
    motoboy = db.Column(db.String(120), index=True)
    entregas = db.Column(db.Integer, default=0)
    km_total = db.Column(db.Float, default=0.0)
    
    # Armazena os números dos pedidos (ex: #101, #102)
    pedidos = db.Column(db.Text) 

    valor_original = db.Column(db.Float, default=0.0)
    ajuste = db.Column(db.Float, default=0.0)
    valor_final = db.Column(db.Float, default=0.0)
    motivo_ajuste = db.Column(db.String(255))