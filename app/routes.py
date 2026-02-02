from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for
from flask_login import login_required
from sqlalchemy import func, extract
from datetime import datetime, timedelta
import pandas as pd
import json, os

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
# DASHBOARD PRINCIPAL
# ======================================================

@bp.route("/")
@login_required
def home():
    return redirect(url_for("main.dashboard"))

@bp.route("/dashboard")
@login_required
def dashboard():
    loja_sel = request.args.get("loja")
    turno_sel = request.args.get("turno")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    q = Historico.query
    if loja_sel: q = q.filter(Historico.loja == loja_sel)
    if turno_sel: q = q.filter(Historico.turno == turno_sel)
    if data_inicio: q = q.filter(func.date(Historico.data) >= data_inicio)
    if data_fim: q = q.filter(func.date(Historico.data) <= data_fim)

    stats = q.with_entities(
        func.sum(Historico.total).label("pago"),
        func.sum(Historico.faturamento_pedidos).label("faturamento"),
        func.sum(Historico.taxas_clientes).label("taxas_cli")
    ).first()

    fin_geral = {
        "faturamento": float(stats.faturamento or 0),
        "taxas_clientes": float(stats.taxas_cli or 0)
    }
    total_geral = float(stats.pago or 0)
    qtd_calculos = q.count()

    por_loja = db.session.query(
        Historico.loja, 
        func.sum(Historico.total)
    ).filter(Historico.id.in_([h.id for h in q.all()]) if qtd_calculos > 0 else False)\
     .group_by(Historico.loja).all()

    cfg = load_config()
    todas_lojas = list(cfg["lojas"].keys())

    return render_template("dashboard.html", 
                           total_geral=total_geral, 
                           fin_geral=fin_geral,
                           qtd_calculos=qtd_calculos, 
                           por_loja=por_loja, 
                           todas_lojas=todas_lojas,
                           request=request)

# ======================================================
# RANKING DE MOTOBOYS
# ======================================================

@bp.route("/dashboard-motoboys")
@login_required
def dashboard_motoboys():
    loja = request.args.get("loja")
    turno = request.args.get("turno")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    q = HistoricoMotoboy.query
    if loja: q = q.filter(HistoricoMotoboy.loja == loja)
    if turno: q = q.filter(HistoricoMotoboy.turno == turno)
    if data_inicio: q = q.filter(func.date(HistoricoMotoboy.data) >= data_inicio)
    if data_fim: q = q.filter(func.date(HistoricoMotoboy.data) <= data_fim)

    dados = q.with_entities(
        HistoricoMotoboy.motoboy,
        func.sum(HistoricoMotoboy.entregas).label("entregas"),
        func.sum(HistoricoMotoboy.km_total).label("km_total"),
        func.sum(HistoricoMotoboy.valor_final).label("total")
    ).group_by(HistoricoMotoboy.motoboy).order_by(func.sum(HistoricoMotoboy.valor_final).desc()).all()

    return render_template("dashboard_motoboys.html", dados=dados, loja=loja, turno=turno, 
                           data_inicio=data_inicio, data_fim=data_fim)

# ======================================================
# PROCESSO DE CÁLCULO
# ======================================================

@bp.route("/calcular-rotas")
@login_required
def calcular_rotas():
    cfg = load_config()
    return render_template("calcular.html", lojas=cfg["lojas"], base=cfg["valor_base"], 
                           km=cfg["valor_km"], minimo=cfg["valor_minimo"])

@bp.route("/calcular-preview", methods=["POST"])
@login_required
def calcular_preview():
    cfg = load_config()
    loja_key = request.form.get("loja")
    loja_cfg = cfg["lojas"].get(loja_key)
    
    if not loja_cfg:
        return jsonify({"error": "Loja inválida"}), 400
        
    origem = loja_cfg["endereco"]
    arquivo = request.files.get("planilha")

    if not arquivo or arquivo.filename == '':
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    try:
        if arquivo.filename.endswith('.csv'):
            try:
                df = pd.read_csv(arquivo, encoding='utf-8', sep=None, engine='python')
            except:
                arquivo.seek(0)
                df = pd.read_csv(arquivo, encoding='latin-1', sep=None, engine='python')
        else:
            df = pd.read_excel(arquivo)
    except Exception as e:
        return jsonify({"error": f"Erro na leitura: {str(e)}"}), 400

    cache = load_cache(CACHE_FILE)
    resumo, financeiro = calcular_pagamentos(
        df, origem, 
        float(request.form.get("base", 0)), 
        float(request.form.get("km", 0)), 
        float(request.form.get("minimo", 0)), 
        cache
    )
    
    save_cache(CACHE_FILE, cache)
    return jsonify({"loja": loja_key, "resumo": resumo, "financeiro": financeiro})

@bp.route("/calcular-confirmar", methods=["POST"])
@login_required
def calcular_confirmar():
    data = request.json
    resumo = data.get("resumo", [])
    fin = data.get("financeiro", {})
    
    historico = Historico(
        loja=data.get("loja", "Desconhecida"),
        total=0,
        turno=resumo[0].get("turno", "Jantar") if resumo else "Jantar",
        faturamento_pedidos=float(fin.get("faturamento", 0)),
        taxas_clientes=float(fin.get("taxas_clientes", 0))
    )
    
    try:
        db.session.add(historico)
        db.session.flush()

        total_geral = 0
        ajustes = data.get("ajustes", {})

        for r in resumo:
            nome = r["entregador"]
            aj_v = float(ajustes.get(nome, {}).get("valor", 0) or 0)
            v_orig = float(r.get("total", 0))
            
            m = HistoricoMotoboy(
                historico_id=historico.id, loja=historico.loja, motoboy=nome,
                entregas=int(r.get("entregas", 0)),
                km_total=float(r.get("media_km", 0)) * int(r.get("entregas", 0)),
                valor_original=v_orig, ajuste=aj_v, valor_final=v_orig + aj_v,
                motivo_ajuste=ajustes.get(nome, {}).get("motivo", ""),
                turno=r.get("turno", historico.turno),
                pedidos=r.get("pedidos", "")
            )
            db.session.add(m)
            total_geral += (v_orig + aj_v)

        historico.total = total_geral
        db.session.commit()

        historico.arquivo_txt = gerar_txt(historico.id)
        historico.arquivo_pdf = gerar_pdf(historico.id)
        db.session.commit()

        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500

# ======================================================
# HISTÓRICO E GESTÃO
# ======================================================

@bp.route("/historico")
@login_required
def historico():
    loja = request.args.get("loja")
    turno = request.args.get("turno")
    data_f = request.args.get("data")

    q = Historico.query
    if loja: q = q.filter(Historico.loja == loja)
    if turno: q = q.filter(Historico.turno == turno)
    if data_f:
        try:
            dt = datetime.strptime(data_f, '%Y-%m-%d').date()
            q = q.filter(func.date(Historico.data) == dt)
        except: pass

    registros = q.order_by(Historico.data.desc()).all()
    cfg = load_config()
    return render_template("historico.html", registros=registros, todas_lojas=list(cfg["lojas"].keys()))

@bp.route("/historico/detalhes/<int:id>")
@login_required
def historico_detalhes(id):
    h = db.session.get(Historico, id)
    if not h: return jsonify({"error": "Não encontrado"}), 404
    
    cobertura = (h.taxas_clientes / h.total * 100) if h.total and h.total > 0 else 0

    dados = []
    for m in h.motoboys:
        km_medio_calculado = (m.km_total / m.entregas) if m.entregas > 0 else 0
        dados.append({
            "id": m.id, 
            "motoboy": m.motoboy, 
            "entregas": m.entregas,
            "km_medio": round(km_medio_calculado, 2),
            "valor_final": m.valor_final,
            "motivo": m.motivo_ajuste, # Envia o motivo salvo
            "pedidos": m.pedidos       # Envia a lista de IDs dos pedidos
        })

    return jsonify({
        "id": h.id, 
        "loja": h.loja.upper(), 
        "turno": h.turno, 
        "data": h.data.strftime("%d/%m/%Y %H:%M"), 
        "faturamento": h.faturamento_pedidos, 
        "taxas_clientes": h.taxas_clientes,
        "pago_motoboys": h.total,
        "cobertura": round(cobertura, 2),
        "dados": dados
    })

@bp.route("/historico/editar", methods=["POST"])
@login_required
def historico_editar():
    data = request.json
    try:
        total_historico = 0
        historico_id = None

        for item in data.get("dados", []):
            m = db.session.get(HistoricoMotoboy, item["id"])
            if m:
                m.valor_final = float(item["valor"])
                m.motivo_ajuste = item.get("motivo", "")
                total_historico += m.valor_final
                historico_id = m.historico_id
        
        # Atualiza o total geral do registro pai
        if historico_id:
            h = db.session.get(Historico, historico_id)
            if h: h.total = total_historico

        db.session.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500

@bp.route("/historico/excluir/<int:id>", methods=["POST"])
@login_required
def historico_excluir(id):
    h = db.session.get(Historico, id)
    if not h:
        return jsonify({"ok": False, "message": "Registro não encontrado"}), 404
        
    try:
        for f in [h.arquivo_txt, h.arquivo_pdf]:
            if f and os.path.exists(f): 
                os.remove(f)
        
        db.session.delete(h)
        db.session.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500

# ======================================================
# NOVAS ROTAS ADICIONADAS (FECHAMENTO E RELATÓRIO)
# ======================================================

@bp.route("/fechamento")
@login_required
def fechamento():
    loja = request.args.get("loja")
    hoje = datetime.now()
    ano = int(request.args.get("ano", hoje.year))
    mes = int(request.args.get("mes", hoje.month))
    
    q = db.session.query(
        HistoricoMotoboy.motoboy,
        func.sum(HistoricoMotoboy.entregas).label("entregas"),
        func.sum(HistoricoMotoboy.km_total).label("km"),
        func.sum(HistoricoMotoboy.valor_final).label("total")
    ).filter(
        extract("year", HistoricoMotoboy.data) == ano,
        extract("month", HistoricoMotoboy.data) == mes
    )
    
    if loja: q = q.filter(HistoricoMotoboy.loja == loja)
    dados = q.group_by(HistoricoMotoboy.motoboy).all()
    
    cfg = load_config()
    return render_template("fechamento.html", 
                           dados=dados, 
                           total_mes=sum(d.total for d in dados), 
                           loja=loja, mes=mes, ano=ano,
                           todas_lojas=list(cfg["lojas"].keys()))

@bp.route("/relatorios")
@login_required
def relatorios_exportar():
    q = Historico.query
    registros = q.all()
    if not registros: return "Sem dados", 404

    data = [{
        "Data": r.data.strftime("%d/%m/%Y"),
        "Loja": r.loja,
        "Turno": r.turno,
        "Faturamento": r.faturamento_pedidos,
        "Taxas Clientes": r.taxas_clientes,
        "Total Pago": r.total
    } for r in registros]

    df = pd.DataFrame(data)
    path = os.path.join(EXPORT_DIR, "relatorio_geral.xlsx")
    df.to_excel(path, index=False)
    return send_file(path, as_attachment=True)

@bp.route("/download")
@login_required
def download():
    path = request.args.get("path")
    if not path or not os.path.exists(path): return "Arquivo não encontrado", 404
    return send_file(os.path.abspath(path), as_attachment=True)