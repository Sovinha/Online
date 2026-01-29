from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for
from flask_login import login_required
from sqlalchemy import func, extract
from datetime import datetime
import pandas as pd
import json
import os

from app.extensions import db
from app.models import Historico, HistoricoMotoboy
from app.services.calculator import calcular_pagamentos
from app.services.cache import load_cache, save_cache
from app.services.history import gerar_txt
from app.services.pdf import gerar_pdf

bp = Blueprint("main", __name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
CACHE_FILE = os.path.join(BASE_DIR, "cache_distancias.json")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")

os.makedirs(EXPORT_DIR, exist_ok=True)

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ======================================================
# HOME
# ======================================================

@bp.route("/")
@login_required
def home():
    return redirect(url_for("main.dashboard"))

# ======================================================
# DASHBOARD
# ======================================================

@bp.route("/dashboard")
@login_required
def dashboard():
    loja = request.args.get("loja")

    q = Historico.query
    if loja:
        q = q.filter(Historico.loja == loja)

    total_geral = q.with_entities(func.sum(Historico.total)).scalar() or 0
    qtd_calculos = q.count()

    por_loja = (
        db.session.query(Historico.loja, func.sum(Historico.total))
        .group_by(Historico.loja)
        .all()
    )

    return render_template(
        "dashboard.html",
        total_geral=total_geral,
        qtd_calculos=qtd_calculos,
        por_loja=por_loja,
        loja=loja
    )

# ======================================================
# DASHBOARD MOTOBOYS
# ======================================================

@bp.route("/dashboard-motoboys")
@login_required
def dashboard_motoboys():
    loja = request.args.get("loja")

    q = HistoricoMotoboy.query
    if loja:
        q = q.filter(HistoricoMotoboy.loja == loja)

    dados = (
        q.with_entities(
            HistoricoMotoboy.motoboy,
            func.sum(HistoricoMotoboy.entregas).label("entregas"),
            func.avg(HistoricoMotoboy.km_total / HistoricoMotoboy.entregas).label("km_medio"),
            func.sum(HistoricoMotoboy.valor_final).label("total")
        )
        .group_by(HistoricoMotoboy.motoboy)
        .order_by(func.sum(HistoricoMotoboy.valor_final).desc())
        .all()
    )

    return render_template(
        "dashboard_motoboys.html",
        dados=dados,
        loja=loja
    )

# ======================================================
# CALCULAR
# ======================================================

@bp.route("/calcular-rotas")
@login_required
def calcular_rotas():
    cfg = load_config()
    return render_template(
        "calcular.html",
        lojas=cfg["lojas"],
        base=cfg["valor_base"],
        km=cfg["valor_km"],
        minimo=cfg["valor_minimo"]
    )

@bp.route("/calcular-preview", methods=["POST"])
@login_required
def calcular_preview():
    cfg = load_config()
    loja_key = request.form["loja"]
    loja_cfg = cfg["lojas"][loja_key]

    df = pd.read_excel(request.files["planilha"])
    cache = load_cache(CACHE_FILE)

    _, resumo = calcular_pagamentos(
        df,
        loja_cfg["endereco"],
        float(request.form["base"]),
        float(request.form["km"]),
        float(request.form["minimo"]),
        cache
    )

    save_cache(CACHE_FILE, cache)

    return jsonify({"loja": loja_key, "resumo": resumo})

@bp.route("/calcular-confirmar", methods=["POST"])
@login_required
def calcular_confirmar():
    data = request.json
    loja = data["loja"]
    resumo = data["resumo"]
    ajustes = data.get("ajustes", {})

    historico = Historico(loja=loja, total=0)
    db.session.add(historico)
    db.session.flush()

    total = 0
    for r in resumo:
        a = ajustes.get(r["entregador"], {})
        ajuste = float(a.get("valor", 0))
        motivo = a.get("motivo", "")

        valor_final = r["total"] + ajuste

        db.session.add(HistoricoMotoboy(
            historico_id=historico.id,
            loja=loja,
            motoboy=r["entregador"],
            entregas=r["entregas"],
            km_total=r["media_km"] * r["entregas"],
            valor_original=r["total"],
            ajuste=ajuste,
            valor_final=valor_final,
            motivo_ajuste=motivo
        ))

        total += valor_final

    historico.total = total
    historico.arquivo_txt = gerar_txt(historico.id)
    historico.arquivo_pdf = gerar_pdf(historico.id)

    db.session.commit()
    return jsonify({"ok": True})

# ======================================================
# HISTÓRICO
# ======================================================

@bp.route("/historico")
@login_required
def historico():
    registros = Historico.query.order_by(Historico.data.desc()).all()
    return render_template("historico.html", registros=registros)

@bp.route("/historico/detalhes/<int:id>")
@login_required
def historico_detalhes(id):
    h = Historico.query.get_or_404(id)

    dados = []
    for m in h.motoboys:
        dados.append({
            "id": m.id,
            "motoboy": m.motoboy,
            "entregas": m.entregas,
            "km_medio": round(m.km_total / m.entregas, 2),
            "valor_original": m.valor_original,
            "ajuste": m.ajuste,
            "valor_final": m.valor_final,
            "motivo": m.motivo_ajuste or ""
        })

    return jsonify({
        "id": h.id,
        "loja": h.loja,
        "data": h.data.strftime("%d/%m/%Y %H:%M"),
        "dados": dados
    })

@bp.route("/historico/editar", methods=["POST"])
@login_required
def historico_editar():
    payload = request.json
    historico = Historico.query.get_or_404(payload["id"])

    total = 0
    for item in payload["itens"]:
        m = HistoricoMotoboy.query.get(item["id"])
        m.valor_final = float(item["valor_final"])
        m.ajuste = m.valor_final - m.valor_original
        m.motivo_ajuste = item.get("motivo", "")
        total += m.valor_final

    historico.total = total
    historico.arquivo_txt = gerar_txt(historico.id)
    historico.arquivo_pdf = gerar_pdf(historico.id)

    db.session.commit()
    return jsonify({"ok": True})

# ======================================================
# FECHAMENTO MENSAL (CORRIGIDO)
# ======================================================

@bp.route("/fechamento")
@login_required
def fechamento():
    loja = request.args.get("loja")  # opcional
    ano = int(request.args.get("ano", datetime.now().year))
    mes = int(request.args.get("mes", datetime.now().month))

    q = HistoricoMotoboy.query.filter(
        extract("year", HistoricoMotoboy.data) == ano,
        extract("month", HistoricoMotoboy.data) == mes
    )

    if loja:
        q = q.filter(HistoricoMotoboy.loja == loja)

    dados = (
        q.with_entities(
            HistoricoMotoboy.motoboy,
            func.sum(HistoricoMotoboy.entregas),
            func.sum(HistoricoMotoboy.km_total),
            func.sum(HistoricoMotoboy.valor_final)
        )
        .group_by(HistoricoMotoboy.motoboy)
        .order_by(func.sum(HistoricoMotoboy.valor_final).desc())
        .all()
    )

    total_mes = sum(d[3] for d in dados)

    return render_template(
        "fechamento.html",
        dados=dados,
        total_mes=total_mes,
        loja=loja,
        mes=mes,
        ano=ano
    )

# ======================================================
# RELATÓRIOS FINANCEIROS (CORRIGIDO)
# ======================================================

@bp.route("/relatorios")
@login_required
def relatorios():
    loja = request.args.get("loja")

    q = Historico.query
    if loja:
        q = q.filter(Historico.loja == loja)

    registros = q.order_by(Historico.data.desc()).all()
    return render_template("relatorios.html", registros=registros, loja=loja)

@bp.route("/relatorios/exportar")
@login_required
def relatorios_exportar():
    loja = request.args.get("loja")

    q = Historico.query
    if loja:
        q = q.filter(Historico.loja == loja)

    df = pd.read_sql(q.statement, db.session.bind)
    path = os.path.join(EXPORT_DIR, "relatorio_financeiro.xlsx")
    df.to_excel(path, index=False)

    return send_file(path, as_attachment=True)

# ======================================================
# DOWNLOAD
# ======================================================

@bp.route("/download")
@login_required
def download():
    return send_file(os.path.abspath(request.args["path"]), as_attachment=True)
