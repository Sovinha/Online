import googlemaps
from collections import defaultdict
import os, json, unicodedata, re
import pandas as pd

def get_base_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def load_api_key():
    config_path = os.path.join(get_base_dir(), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)["google_maps_api_key"]

gmaps = googlemaps.Client(key=load_api_key())

def normalizar(texto):
    if not texto: return ""
    texto = str(texto).lower().strip()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return re.sub(r'[^a-z0-9 ]', '', texto)

def identificar_turno(data_str):
    try:
        dt = pd.to_datetime(data_str)
        return "Almoço" if 5 <= dt.hour < 16 else "Jantar"
    except:
        return "Jantar"

def limpar_valor_monetario(valor):
    """Converte 'R$ 25,50' ou '25.50' em float 25.50"""
    if pd.isna(valor) or valor == "": return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    # Remove símbolos e ajusta separadores decimais
    s = str(valor).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".").strip()
    try: return float(s)
    except: return 0.0

def calcular_distancia_segura(origem, destino, cache):
    chave = f"{normalizar(origem)}->{normalizar(destino)}"
    if chave in cache: return cache[chave]
    try:
        result = gmaps.distance_matrix(origem, destino)
        element = result["rows"][0]["elements"][0]
        if element.get("status") == "OK":
            km = element["distance"]["value"] / 1000
            cache[chave] = km
            return km
    except Exception as e:
        print(f"Erro API: {e}")
    return None

def calcular_pagamentos(df, origem, base, valor_km, minimo, cache):
    entregadores = defaultdict(lambda: {"total": 0, "entregas": 0, "dist": 0, "turno": "Jantar", "pedidos_list": []})
    faturamento_bruto = 0.0
    taxas_pagas_clientes = 0.0

    # Localiza colunas por nomes aproximados (iFood, Rappi, Próprio)
    col_fat = next((c for c in df.columns if 'valor' in c.lower() and 'pedido' in c.lower()), "Valor do pedido")
    col_taxa = next((c for c in df.columns if 'taxa' in c.lower() and 'entrega' in c.lower()), "Taxa de entrega")
    id_col = next((c for c in df.columns if 'id' in c.lower() or 'numero' in c.lower()), "Id do pedido")

    if id_col in df.columns:
        df = df.drop_duplicates(subset=[id_col])

    for _, row in df.iterrows():
        rua = str(row.get("Rua", "")).strip()
        if not rua or rua.lower() == "nan": continue
        
        # CAPTURA FINANCEIRA CORRIGIDA
        faturamento_bruto += limpar_valor_monetario(row.get(col_fat, 0))
        taxas_pagas_clientes += limpar_valor_monetario(row.get(col_taxa, 0))

        # CÁLCULO DE ENTREGA
        numero = str(row.get("Número") or row.get("Numero") or "")
        bairro = str(row.get("Bairro") or "")
        cidade = str(row.get("Cidade") or "")
        endereco_completo = f"{rua}, {numero} - {bairro}, {cidade}"
        
        km = calcular_distancia_segura(origem, endereco_completo, cache)
        
        if km is not None:
            valor_entrega = max((base + (km * valor_km)), minimo)
            nome = str(row.get("Entregador", "Desconhecido")).strip()
            turno = identificar_turno(row.get("Data de criação"))
            id_ped = str(row.get(id_col, "S/N"))

            chave_id = f"{nome}_{turno}"
            entregadores[chave_id]["total"] += valor_entrega
            entregadores[chave_id]["entregas"] += 1
            entregadores[chave_id]["dist"] += km
            entregadores[chave_id]["entregador_nome"] = nome
            entregadores[chave_id]["turno"] = turno
            entregadores[chave_id]["pedidos_list"].append(id_ped)

    resumo = []
    for d in entregadores.values():
        resumo.append({
            "entregador": d["entregador_nome"],
            "total": round(d["total"], 2),
            "entregas": d["entregas"],
            "media_km": round(d["dist"] / d["entregas"], 2) if d["entregas"] > 0 else 0,
            "turno": d["turno"],
            "pedidos": ", ".join(d["pedidos_list"])
        })

    return resumo, {"faturamento": round(faturamento_bruto, 2), "taxas_clientes": round(taxas_pagas_clientes, 2)}