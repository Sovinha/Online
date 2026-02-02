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

# Inicialização segura da API
try:
    gmaps = googlemaps.Client(key=load_api_key())
except Exception as e:
    print(f"Erro ao iniciar Google Maps: {e}")

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
    if pd.isna(valor) or valor == "" or valor is None: return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    try:
        s = str(valor).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".").strip()
        return float(s)
    except:
        return 0.0

def calcular_distancia_segura(origem, destino, cache):
    if not destino or len(destino) < 5: return None
    chave = f"{normalizar(origem)}->{normalizar(destino)}"
    if chave in cache: return cache[chave]
    try:
        result = gmaps.distance_matrix(origem, destino)
        if result["status"] == "OK":
            element = result["rows"][0]["elements"][0]
            if element.get("status") == "OK":
                km = element["distance"]["value"] / 1000
                cache[chave] = km
                return km
    except Exception as e:
        print(f"Erro API Google: {e}")
    return None

def calcular_pagamentos(df, origem, base, valor_km, minimo, cache):
    entregadores = defaultdict(lambda: {"total": 0, "entregas": 0, "dist": 0, "turno": "Jantar", "pedidos_list": []})
    
    # 1. Identificação Robusta de Colunas
    cols = [str(c) for c in df.columns]
    
    # --- NOVA LÓGICA DE IDENTIFICAÇÃO DE ID ---
    # Passo A: Tenta achar colunas que NÃO tenham "ID" no nome (prioriza 'Número', 'Nº', 'Pedido')
    id_col = next((c for c in cols if any(x in c.lower() for x in ['numero', 'nº', 'pedido']) and 'id' not in c.lower()), None)
    
    # Passo B: Se não achou, aí sim aceita qualquer uma que tenha 'id', 'numero', etc.
    if not id_col:
        id_col = next((c for c in cols if any(x in c.lower() for x in ['id', 'numero', 'nº', 'pedido'])), None)
    # ------------------------------------------
    
    col_fat = next((c for c in cols if 'valor' in c.lower() and 'pedido' in c.lower()), None)
    col_taxa = next((c for c in cols if 'taxa' in c.lower() and 'entrega' in c.lower()), None)
    col_entregador = next((c for c in cols if 'entregador' in c.lower() or 'motoboy' in c.lower()), "Entregador")

    # 2. Tratamento de Duplicados
    if id_col:
        df = df.drop_duplicates(subset=[id_col]).copy()

    faturamento_bruto = 0.0
    taxas_pagas_clientes = 0.0

    # 3. Processamento das Linhas
    for _, row in df.iterrows():
        if col_fat: faturamento_bruto += limpar_valor_monetario(row.get(col_fat, 0))
        if col_taxa: taxas_pagas_clientes += limpar_valor_monetario(row.get(col_taxa, 0))

        rua = str(row.get("Rua", "")).strip()
        if not rua or rua.lower() in ["nan", "none", ""]: continue
        
        numero = str(row.get("Número") or row.get("Numero") or "")
        bairro = str(row.get("Bairro") or "")
        cidade = str(row.get("Cidade") or "")
        endereco_completo = f"{rua}, {numero} - {bairro}, {cidade}"
        
        km = calcular_distancia_segura(origem, endereco_completo, cache)
        
        if km is not None:
            valor_entrega = max((base + (km * valor_km)), minimo)
            nome = str(row.get(col_entregador, "Desconhecido")).strip()
            
            data_raw = row.get("Data de criação") or row.get("Data") or ""
            turno = identificar_turno(data_raw)
            
            # Formatação do ID do pedido para remover .0 (ex: 15.0 vira 15)
            id_ped_raw = row.get(id_col, "S/N")
            if pd.isna(id_ped_raw) or id_ped_raw == "":
                id_ped = "S/N"
            else:
                try:
                    # Converte para int e depois string para limpar o ".0"
                    id_ped = str(int(float(id_ped_raw)))
                except:
                    id_ped = str(id_ped_raw)

            chave_id = f"{nome}_{turno}"
            entregadores[chave_id]["total"] += valor_entrega
            entregadores[chave_id]["entregas"] += 1
            entregadores[chave_id]["dist"] += km
            entregadores[chave_id]["entregador_nome"] = nome
            entregadores[chave_id]["turno"] = turno
            entregadores[chave_id]["pedidos_list"].append(id_ped)

    # 4. Formatação do Resumo Final
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

    return resumo, {
        "faturamento": round(faturamento_bruto, 2), 
        "taxas_clientes": round(taxas_pagas_clientes, 2)
    }