from datetime import datetime
from flask_login import UserMixin
from app.extensions import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Historico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, default=datetime.now)
    loja = db.Column(db.String(50), index=True)
    total = db.Column(db.Float)

    arquivo_txt = db.Column(db.String(255))
    arquivo_pdf = db.Column(db.String(255))

    motoboys = db.relationship(
        "HistoricoMotoboy",
        backref="historico",
        cascade="all, delete-orphan"
    )

class HistoricoMotoboy(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    historico_id = db.Column(
        db.Integer,
        db.ForeignKey("historico.id"),
        nullable=False,
        index=True
    )

    data = db.Column(db.DateTime, default=datetime.now)
    loja = db.Column(db.String(50), index=True)
    motoboy = db.Column(db.String(120), index=True)

    entregas = db.Column(db.Integer)
    km_total = db.Column(db.Float)

    valor_original = db.Column(db.Float)
    ajuste = db.Column(db.Float)
    valor_final = db.Column(db.Float)

    motivo_ajuste = db.Column(db.String(255))
