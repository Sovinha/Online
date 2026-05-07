from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import login_required, current_user, login_user, logout_user
from sqlalchemy import func, text
from werkzeug.security import check_password_hash
import pandas as pd
from io import BytesIO
from datetime import datetime
from calendar import monthrange
from app.config import CACHE_FILE, load_config
from app.extensions import db
from app.models import User, Historico, HistoricoMotoboy, ItemCompra, get_br_time

bp = Blueprint("main", __name__)


# ======================================================
# AUTENTICAÇÃO
# ======================================================

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u, p = request.form.get("username"), request.form.get("password")
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password, p):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        flash("Usuário ou senha inválidos", "danger")
    return render_template("login.html")

@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.colaborador_selecao"))

@bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("main.colaborador_selecao"))

# ======================================================
# DASHBOARDS
# ======================================================

@bp.route("/dashboard")
@login_required
def dashboard():
    hoje = get_br_time().date()
    primeiro_dia_mes = hoje.replace(day=1)
    ultimo_dia_mes = hoje.replace(day=monthrange(hoje.year, hoje.month)[1])

    data_inicio = request.args.get("data_inicio") or primeiro_dia_mes.isoformat()
    data_fim = request.args.get("data_fim") or ultimo_dia_mes.isoformat()
    loja_sel = request.args.get("loja")
    turno_sel = request.args.get("turno")
    q = Historico.query
    if loja_sel:
        q = q.filter(Historico.loja == loja_sel)
    if turno_sel:
        q = q.filter(Historico.turno == turno_sel)
    if data_inicio:
        q = q.filter(func.date(Historico.data) >= data_inicio)
    if data_fim:
        q = q.filter(func.date(Historico.data) <= data_fim)

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
    
    por_loja_query = db.session.query(Historico.loja, func.sum(Historico.total))
    if loja_sel:
        por_loja_query = por_loja_query.filter(Historico.loja == loja_sel)
    if turno_sel:
        por_loja_query = por_loja_query.filter(Historico.turno == turno_sel)
    if data_inicio:
        por_loja_query = por_loja_query.filter(func.date(Historico.data) >= data_inicio)
    if data_fim:
        por_loja_query = por_loja_query.filter(func.date(Historico.data) <= data_fim)
    por_loja = por_loja_query.group_by(Historico.loja).all()

    mes_anterior_ano = hoje.year if hoje.month > 1 else hoje.year - 1
    mes_anterior_mes = hoje.month - 1 if hoje.month > 1 else 12
    mes_anterior_inicio = hoje.replace(year=mes_anterior_ano, month=mes_anterior_mes, day=1)
    mes_anterior_fim = hoje.replace(
        year=mes_anterior_ano,
        month=mes_anterior_mes,
        day=monthrange(mes_anterior_ano, mes_anterior_mes)[1]
    )

    cfg = load_config()
    
    return render_template("dashboard.html", 
                           total_geral=total_geral, 
                           fin_geral=fin_geral, 
                           por_loja=por_loja, 
                           todas_lojas=list(cfg.get("lojas", {}).keys()),
                           filtro_data_inicio=data_inicio,
                           filtro_data_fim=data_fim,
                           filtro_turno=turno_sel or "",
                           mes_atual_inicio=primeiro_dia_mes.isoformat(),
                           mes_atual_fim=ultimo_dia_mes.isoformat(),
                           mes_anterior_inicio=mes_anterior_inicio.isoformat(),
                           mes_anterior_fim=mes_anterior_fim.isoformat(),
                           request=request)

@bp.route("/dashboard/motoboys")
@login_required
def dashboard_motoboys():
    hoje = get_br_time().date()
    primeiro_dia_mes = hoje.replace(day=1)
    ultimo_dia_mes = hoje.replace(day=monthrange(hoje.year, hoje.month)[1])

    cfg = load_config()
    loja = request.args.get("loja")
    data_inicio = request.args.get("data_inicio") or primeiro_dia_mes.isoformat()
    data_fim = request.args.get("data_fim") or ultimo_dia_mes.isoformat()

    q = db.session.query(
        HistoricoMotoboy.motoboy,
        func.sum(HistoricoMotoboy.entregas).label('total_entregas'),
        func.avg(HistoricoMotoboy.km_total / func.nullif(HistoricoMotoboy.entregas, 0)).label('km_medio'),
        func.sum(HistoricoMotoboy.valor_final).label('faturamento_total')
    )

    if loja: q = q.filter(HistoricoMotoboy.loja == loja)
    if data_inicio: q = q.filter(func.date(HistoricoMotoboy.data) >= data_inicio)
    if data_fim: q = q.filter(func.date(HistoricoMotoboy.data) <= data_fim)

    dados = q.group_by(HistoricoMotoboy.motoboy).order_by(func.sum(HistoricoMotoboy.entregas).desc()).all()
    total_pago = sum(d[3] for d in dados) if dados else 0
    total_pedidos = sum(d[1] for d in dados) if dados else 0

    return render_template("dashboard_motoboys.html", 
                           dados=dados, total_pago=total_pago, total_pedidos=total_pedidos,
                           loja=loja, data_inicio=data_inicio, data_fim=data_fim,
                           todas_lojas=list(cfg.get("lojas", {}).keys()))

# ======================================================
# CÁLCULOS E HISTÓRICO
# ======================================================

@bp.route("/calcular-rotas")
@login_required
def calcular_rotas():
    cfg = load_config()
    return render_template("calcular.html", lojas=cfg["lojas"], base=cfg["valor_base"], km=cfg["valor_km"], minimo=cfg["valor_minimo"])

@bp.route("/conferencia-pedidos")
@login_required
def conferencia_pedidos():
    return render_template("conferencia_pedidos.html")

@bp.route("/conferencia-pedidos/analisar", methods=["POST"])
@login_required
def conferencia_pedidos_analisar():
    from app.services.report_compare import compare_reports

    arquivo_cardapio = request.files.get("planilha_cardapio")
    arquivo_food = request.files.get("planilha_food")

    if not arquivo_cardapio or not arquivo_food:
        return jsonify({"error": "Envie as duas planilhas para comparar."}), 400

    try:
        df_cardapio = pd.read_excel(arquivo_cardapio)
        df_food = pd.read_excel(arquivo_food)
        resultado = compare_reports(df_cardapio, df_food)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@bp.route("/calcular-preview", methods=["POST"])
@login_required
def calcular_preview():
    from app.services.calculator import calcular_pagamentos, DistanceServiceUnavailable
    from app.services.cache import load_cache, save_cache
    cfg = load_config()
    loja_key = request.form.get("loja")
    arquivo = request.files.get("planilha")
    
    if not arquivo:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    df = pd.read_excel(arquivo) if arquivo.filename.endswith('.xlsx') else pd.read_csv(arquivo)
    cache = load_cache(CACHE_FILE)

    try:
        resumo, financeiro = calcular_pagamentos(
            df, cfg["lojas"][loja_key]["endereco"], 
            float(request.form.get("base")), float(request.form.get("km")), 
            float(request.form.get("minimo")), cache
        )
    except DistanceServiceUnavailable as e:
        return jsonify({"error": str(e)}), 503

    save_cache(CACHE_FILE, cache)
    return jsonify({"loja": loja_key, "resumo": resumo, "financeiro": financeiro})

@bp.route("/calcular-confirmar", methods=["POST"])
@login_required
def calcular_confirmar():
    data = request.json
    resumo = data.get("resumo", [])
    fin = data.get("financeiro", {})
    ajustes = data.get("ajustes", {})

    try:
        resumo_por_turno = {}
        financeiro_por_turno = fin.get("por_turno", {})

        for item in resumo:
            resumo_por_turno.setdefault(item.get("turno", "Jantar"), []).append(item)

        for turno, itens_turno in resumo_por_turno.items():
            fin_turno = financeiro_por_turno.get(turno, {})
            historico = Historico(
                loja=data.get("loja"),
                faturamento_pedidos=float(fin_turno.get("faturamento", 0)),
                taxas_clientes=float(fin_turno.get("taxas_clientes", 0)),
                turno=turno
            )

            db.session.add(historico)
            db.session.flush()

            total_pago_turno = 0
            for r in itens_turno:
                chave_ajuste = r.get("grupo") or r["entregador"]
                aj = ajustes.get(chave_ajuste, {"valor": 0, "motivo": ""})
                v_final = float(r["total"]) + float(aj["valor"])

                m = HistoricoMotoboy(
                    historico_id=historico.id,
                    motoboy=r["entregador"],
                    entregas=int(r["entregas"]),
                    km_total=float(r["media_km"]) * int(r["entregas"]),
                    valor_original=float(r["total"]),
                    ajuste=float(aj["valor"]),
                    valor_final=v_final,
                    motivo_ajuste=aj["motivo"],
                    loja=historico.loja,
                    turno=turno,
                    pedidos=str(r.get("pedidos", ""))
                )
                db.session.add(m)
                total_pago_turno += v_final

            historico.total = total_pago_turno

        db.session.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@bp.route("/historico")
@login_required
def historico():
    cfg = load_config()
    loja, turno, data_f = request.args.get("loja"), request.args.get("turno"), request.args.get("data")
    
    q = Historico.query
    if loja: q = q.filter(Historico.loja == loja)
    if turno: q = q.filter(Historico.turno == turno)
    if data_f: q = q.filter(func.date(Historico.data) == data_f)
    
    registros = q.order_by(Historico.id.desc()).all()
    return render_template("historico.html", registros=registros, loja=loja, turno=turno, 
                           data_filtro=data_f, todas_lojas=list(cfg.get("lojas", {}).keys()))

@bp.route("/historico/detalhes/<int:id>")
@login_required
def historico_detalhes(id):
    h = Historico.query.get_or_404(id)
    detalhes = HistoricoMotoboy.query.filter_by(historico_id=id).all()
    cobertura = (h.taxas_clientes / h.total * 100) if h.total > 0 else 0
    return jsonify({
        "loja": h.loja, "data": h.data.strftime("%d/%m/%Y"), "turno": h.turno,
        "faturamento": h.faturamento_pedidos, "taxas_clientes": h.taxas_clientes,
        "pago_motoboys": h.total, "cobertura": round(cobertura, 2),
        "erros": h.erros, # Importante para o JavaScript
        "dados": [{"id": d.id, "motoboy": d.motoboy, "entregas": d.entregas, 
                   "km_medio": round(d.km_total/d.entregas, 2) if d.entregas > 0 else 0,
                   "valor_final": d.valor_final, "motivo": d.motivo_ajuste, "pedidos": d.pedidos} for d in detalhes]
    })

@bp.route("/historico/salvar-erro/<int:id>", methods=["POST"])
@login_required
def salvar_erro(id):
    try:
        h = Historico.query.get_or_404(id)
        dados = request.json
        h.erros = dados.get("erro")
        db.session.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@bp.route("/historico/editar", methods=["POST"])
@login_required
def historico_editar():
    try:
        dados = request.json.get("dados", [])
        h_id = None
        for item in dados:
            m = HistoricoMotoboy.query.get(item['id'])
            if m:
                m.valor_final = float(item['valor'])
                m.motivo_ajuste = item['motivo']
                h_id = m.historico_id
        if h_id:
            h = Historico.query.get(h_id)
            h.total = db.session.query(func.sum(HistoricoMotoboy.valor_final)).filter_by(historico_id=h_id).scalar()
            db.session.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@bp.route("/historico/excluir/<int:id>", methods=["POST"])
@login_required
def historico_excluir(id):
    try:
        db.session.delete(Historico.query.get_or_404(id))
        db.session.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

# ======================================================
# EXPORTAÇÃO E COMPRAS
# ======================================================

@bp.route("/relatorios/exportar")
@login_required
def relatorios_exportar():
    dados = HistoricoMotoboy.query.all()
    df = pd.DataFrame([{
        "Data": d.data.strftime("%d/%m/%Y"), "Loja": d.loja, "Turno": d.turno,
        "Motoboy": d.motoboy, "Entregas": d.entregas, "Valor Final": d.valor_final,
        "Motivo Ajuste": d.motivo_ajuste
    } for d in dados])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Relatorio')
    output.seek(0)
    return send_file(output, download_name=f"relatorio_{datetime.now().strftime('%Y%m%d')}.xlsx", as_attachment=True)

@bp.route('/colaborador')
def colaborador_selecao():
    return render_template('colaborador_login.html')

@bp.route('/colaborador/lista/<setor>')
def colaborador_lista(setor):
    itens = ItemCompra.query.filter_by(setor=setor.upper()).order_by(ItemCompra.categoria, ItemCompra.nome).all()
    return render_template('colaborador.html', itens=itens, setor=setor.upper())

@bp.route('/add_item/<setor>', methods=['POST'])
def add_item_compra(setor):
    nome = request.form.get('nome')
    cat_digitada = request.form.get('nova_categoria')
    cat_selecionada = request.form.get('categoria')
    categoria_final = (cat_digitada if cat_digitada else cat_selecionada) or 'OUTROS'
    
    if nome:
        novo_item = ItemCompra(nome=nome.upper().strip(), setor=setor.upper(), 
                               categoria=categoria_final.upper().strip(), quantidade=0)
        db.session.add(novo_item)
        db.session.commit()
    return redirect(url_for('main.colaborador_lista', setor=setor))

@bp.route('/update_item_v2/<int:id>', methods=['POST'])
def update_item_v2(id):
    try:
        item = ItemCompra.query.get_or_404(id)
        item.quantidade = int(request.form.get('quantidade', 0))
        item.quem_pediu = request.form.get('colaborador_nome', 'ANÔNIMO').upper()
        item.data = get_br_time() 
        db.session.commit()
        return redirect(request.referrer)
    except Exception:
        db.session.rollback()
        return redirect(request.referrer)

@bp.route('/colaborador/delete/<int:id>', methods=['POST'])
def delete_item(id):
    item = ItemCompra.query.get_or_404(id)
    setor = item.setor
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('main.colaborador_lista', setor=setor))

@bp.route("/admin/compras-geral")
@login_required
def compras_geral():
    itens = ItemCompra.query.filter(ItemCompra.quantidade > 0).order_by(ItemCompra.setor).all()
    return render_template("admin_compras.html", itens=itens)

@bp.route('/admin/limpar-lista/<setor>', methods=['POST'])
@login_required
def limpar_lista(setor):
    q = ItemCompra.query
    if setor != 'TODOS': q = q.filter_by(setor=setor.upper())
    q.update({ItemCompra.quantidade: 0})
    db.session.commit()
    return redirect(url_for('main.compras_geral'))
