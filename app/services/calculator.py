import googlemaps
from collections import defaultdict
import unicodedata
import re
import pandas as pd
from app.config import load_config


class DistanceServiceUnavailable(Exception):
    pass

def load_api_key():
    cfg = load_config()
    api_key = cfg.get("google_maps_api_key")
    if not api_key:
        raise DistanceServiceUnavailable(
            "Google Maps sem chave configurada. Defina GOOGLE_MAPS_API_KEY no ambiente ou no config.json."
        )
    return api_key

gmaps = None

def get_gmaps_client(force_reload=False):
    global gmaps
    if gmaps is None or force_reload:
        gmaps = googlemaps.Client(key=load_api_key())
    return gmaps

# Inicialização segura da API
try:
    get_gmaps_client(force_reload=True)
except Exception as e:
    print(f"Erro ao iniciar Google Maps: {e}")

def normalizar(texto):
    if not texto: return ""
    texto = str(texto).lower().strip()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return re.sub(r'[^a-z0-9 ]', '', texto)

def sanitizar_endereco_consulta(texto):
    if not texto:
        return ""
    texto = unicodedata.normalize('NFKD', str(texto)).encode('ASCII', 'ignore').decode('ASCII')
    return re.sub(r'\s+', ' ', texto).strip()

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
        origem_consulta = sanitizar_endereco_consulta(origem)
        destino_consulta = sanitizar_endereco_consulta(destino)
        result = get_gmaps_client().distance_matrix(origem_consulta, destino_consulta)
        if result["status"] == "OK":
            element = result["rows"][0]["elements"][0]
            if element.get("status") == "OK":
                km = element["distance"]["value"] / 1000
                cache[chave] = km
                return km
    except Exception as e:
        erro = str(e)
        if "REQUEST_DENIED" in erro or "billing" in erro.lower():
            try:
                result = get_gmaps_client(force_reload=True).distance_matrix(origem_consulta, destino_consulta)
                if result["status"] == "OK":
                    element = result["rows"][0]["elements"][0]
                    if element.get("status") == "OK":
                        km = element["distance"]["value"] / 1000
                        cache[chave] = km
                        return km
            except Exception:
                pass
            raise DistanceServiceUnavailable(
                "Google Maps indisponível para novas distâncias. Verifique a chave/API e o faturamento do projeto."
            ) from e
        print(f"Erro API Google: {e}")
    return None

def calcular_pagamentos(df, origem, base, valor_km, minimo, cache):
    entregadores = defaultdict(lambda: {"total": 0, "entregas": 0, "dist": 0, "turno": "Jantar", "pedidos_list": []})
    financeiro_por_turno = defaultdict(lambda: {"faturamento": 0.0, "taxas_clientes": 0.0})
    
    # 1. Identificação Robusta de Colunas
    cols = [str(c) for c in df.columns]
    cols_norm = {str(c): normalizar(c) for c in df.columns}

    def encontrar_coluna(*nomes_esperados):
        esperados = {normalizar(nome) for nome in nomes_esperados}
        for original, normalizada in cols_norm.items():
            if normalizada in esperados:
                return original
        return None
    
    # --- LÓGICA DE IDENTIFICAÇÃO DE ID CURTO (Número do pedido) ---
    # Prioridade 1: Nome exato "Número do pedido" (ajustado conforme sua imagem)
    id_col = next((c for c in cols if normalizar(c) == "numero do pedido"), None)
    
    # Prioridade 2: Se não achou o exato, busca por 'numero' ou 'nº' que não tenha 'id' no nome
    if not id_col:
        id_col = next((c for c in cols if any(x in normalizar(c) for x in ['numero', 'nº', 'pedido']) and 'id' not in normalizar(c)), None)
    
    # Prioridade 3: Backup final aceitando qualquer menção a ID/Pedido
    if not id_col:
        id_col = next((c for c in cols if any(x in normalizar(c) for x in ['id', 'numero', 'nº', 'pedido'])), None)
    # -------------------------------------------------------------
    
    col_fat = next((c for c in cols if 'valor' in c.lower() and 'pedido' in c.lower()), None)
    col_taxa = next((c for c in cols if 'taxa' in c.lower() and 'entrega' in c.lower()), None)
    col_entregador = next((c for c in cols if 'entregador' in c.lower() or 'motoboy' in c.lower()), "Entregador")
    col_rua = encontrar_coluna("Rua")
    col_numero = encontrar_coluna("Número", "Numero")
    col_bairro = encontrar_coluna("Bairro")
    col_cidade = encontrar_coluna("Cidade")
    col_data = encontrar_coluna("Data de criação", "Data de criacao", "Data")

    # 2. Tratamento de Duplicados (Usa o ID curto para não contar o mesmo pedido duas vezes)
    if id_col:
        df = df.drop_duplicates(subset=[id_col]).copy()

    faturamento_bruto = 0.0
    taxas_pagas_clientes = 0.0

    # 3. Processamento das Linhas
    for _, row in df.iterrows():
        data_raw = row.get(col_data) if col_data else ""
        turno = identificar_turno(data_raw)

        valor_pedido = limpar_valor_monetario(row.get(col_fat, 0)) if col_fat else 0.0
        valor_taxa = limpar_valor_monetario(row.get(col_taxa, 0)) if col_taxa else 0.0

        faturamento_bruto += valor_pedido
        taxas_pagas_clientes += valor_taxa
        financeiro_por_turno[turno]["faturamento"] += valor_pedido
        financeiro_por_turno[turno]["taxas_clientes"] += valor_taxa

        rua = str(row.get(col_rua, "")).strip() if col_rua else ""
        if not rua or rua.lower() in ["nan", "none", ""]: continue
        
        numero = str(row.get(col_numero) or "") if col_numero else ""
        bairro = str(row.get(col_bairro) or "") if col_bairro else ""
        cidade = str(row.get(col_cidade) or "") if col_cidade else ""
        endereco_completo = f"{rua}, {numero} - {bairro}, {cidade}"
        
        km = calcular_distancia_segura(origem, endereco_completo, cache)
        
        if km is not None:
            valor_entrega = max((base + (km * valor_km)), minimo)
            nome = str(row.get(col_entregador, "Desconhecido")).strip()

            # Formatação do ID do pedido para remover .0 (ex: 1.0 vira 1)
            id_ped_raw = row.get(id_col, "S/N")
            if pd.isna(id_ped_raw) or id_ped_raw == "":
                id_ped = "S/N"
            else:
                try:
                    # Tenta converter para inteiro para limpar casas decimais se houver
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
            "grupo": f"{normalizar(d['entregador_nome'])}__{normalizar(d['turno'])}",
            "total": round(d["total"], 2),
            "entregas": d["entregas"],
            "media_km": round(d["dist"] / d["entregas"], 2) if d["entregas"] > 0 else 0,
            "turno": d["turno"],
            "pedidos": ", ".join(d["pedidos_list"])
        })

    resumo.sort(key=lambda item: (item["turno"], item["entregador"]))

    return resumo, {
        "faturamento": round(faturamento_bruto, 2), 
        "taxas_clientes": round(taxas_pagas_clientes, 2),
        "por_turno": {
            turno: {
                "faturamento": round(valores["faturamento"], 2),
                "taxas_clientes": round(valores["taxas_clientes"], 2)
            }
            for turno, valores in financeiro_por_turno.items()
        }
    }
