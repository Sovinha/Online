from app.extensions import db
from flask_login import UserMixin
from datetime import datetime
import pytz

def get_br_time():
    return datetime.now(pytz.timezone('America/Sao_Paulo'))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class Historico(db.Model):
    __tablename__ = 'historico'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data = db.Column(db.DateTime, default=get_br_time)
    loja = db.Column(db.String(100))
    total = db.Column(db.Float, default=0.0)
    faturamento_pedidos = db.Column(db.Float, default=0.0)
    taxas_clientes = db.Column(db.Float, default=0.0)
    turno = db.Column(db.String(50))
    erros = db.Column(db.Text)  # <--- ADICIONE ESTA LINHA
    detalhes = db.relationship('HistoricoMotoboy', backref='pai', cascade="all, delete-orphan")

class HistoricoMotoboy(db.Model):
    __tablename__ = 'historico_motoboy'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    historico_id = db.Column(db.Integer, db.ForeignKey('historico.id', ondelete='CASCADE'), nullable=False)
    data = db.Column(db.DateTime, default=get_br_time)
    motoboy = db.Column(db.String(100))
    entregas = db.Column(db.Integer)
    km_total = db.Column(db.Float)
    valor_original = db.Column(db.Float)
    ajuste = db.Column(db.Float, default=0.0)
    valor_final = db.Column(db.Float)
    motivo_ajuste = db.Column(db.String(255))
    loja = db.Column(db.String(100))
    turno = db.Column(db.String(50))
    pedidos = db.Column(db.Text)

class ItemCompra(db.Model):
    __tablename__ = 'item_compra'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    setor = db.Column(db.String(50), nullable=False)
    categoria = db.Column(db.String(50))
    quantidade = db.Column(db.Integer, default=0)
    quem_pediu = db.Column(db.String(100))
    data = db.Column(db.DateTime, default=get_br_time)