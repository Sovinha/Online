import googlemaps
from collections import defaultdict
import os, json, unicodedata, re
import pandas as pd

# ... (funções get_base_dir, load_api_key, normalizar, identificar_turno permanecem iguais)

def limpar_valor_monetario(valor):
    if pd.isna(valor) or valor == "": return 0.0
    if isinstance(valor, (int, float)): return float(valor)
    s = str(valor).replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(s)
    except:
        return 0.0

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
    
    # 1. TRATAMENTO DE DUPLICADAS (Essencial para não triplicar o KM e as Taxas)
    # Procuramos a coluna de ID do pedido para garantir que cada pedido seja processado uma única vez
    id_col = next((c for c in df.columns if any(x in c.lower() for x in ['id', 'numero', 'pedido'])), None)
    
    if id_col:
        df = df.drop_duplicates(subset=[id_col])

    # 2. MAPEAMENTO DE COLUNAS FINANCEIRAS
    # Verifique se os nomes das colunas na sua planilha são exatamente esses
    col_fat = next((c for c in df.columns if 'valor' in c.lower() and 'pedido' in c.lower()), None)
    col_taxa = next((c for c in df.columns if 'taxa' in c.lower() and 'entrega' in c.lower()), None)

    faturamento_bruto = 0.0
    taxas_pagas_clientes = 0.0

    for _, row in df.iterrows():
        rua = str(row.get("Rua", "")).strip()
        if not rua or rua.lower() == "nan": continue
        
        # Captura financeira
        valor_ped = limpar_valor_monetario(row.get(col_fat, 0)) if col_fat else 0.0
        valor_taxa = limpar_valor_monetario(row.get(col_taxa, 0)) if col_taxa else 0.0
        
        faturamento_bruto += valor_ped
        taxas_pagas_clientes += valor_taxa

        # Endereço
        numero = str(row.get("Número") or row.get("Numero") or "")
        bairro = str(row.get("Bairro") or "")
        cidade = str(row.get("Cidade") or "")
        endereco_completo = f"{rua}, {numero} - {bairro}, {cidade}"
        
        km = calcular_distancia_segura(origem, endereco_completo, cache)
        
        if km is not None:
            # O valor pago ao motoboy usa a regra do KM
            valor_pago_motoboy = max((base + (km * valor_km)), minimo)
            
            nome = str(row.get("Entregador", "Desconhecido")).strip()
            turno = identificar_turno(row.get("Data de criação") or row.get("Data"))
            id_ped = str(row.get(id_col, "S/N"))

            chave_id = f"{nome}_{turno}"
            entregadores[chave_id]["total"] += valor_pago_motoboy
            entregadores[chave_id]["entregas"] += 1
            entregadores[chave_id]["dist"] += km # Aqui agora está seguro pois removemos duplicatas
            entregadores[chave_id]["entregador_nome"] = nome
            entregadores[chave_id]["turno"] = turno
            entregadores[chave_id]["pedidos_list"].append(id_ped)

    resumo = []
    for d in entregadores.values():
        resumo.append({
            "entregador": d["entregador_nome"],
            "total": round(d["total"], 2),
            "entregas": d["entregas"],
            # KM Médio real por entrega
            "media_km": round(d["dist"] / d["entregas"], 2) if d["entregas"] > 0 else 0,
            "turno": d["turno"],
            "pedidos": ", ".join(d["pedidos_list"])
        })

    return resumo, {
        "faturamento": round(faturamento_bruto, 2), 
        "taxas_clientes": round(taxas_pagas_clientes, 2)
    }