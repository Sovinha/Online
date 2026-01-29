import googlemaps
from collections import defaultdict
from datetime import datetime
import os
import json

# ======================================================
# LOCALIZAR CONFIG.JSON (COMPATÍVEL COM EXE)
# ======================================================

def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sys
BASE_DIR = get_base_dir()
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# ======================================================
# CARREGAR API KEY (ENV -> CONFIG.JSON)
# ======================================================

def load_api_key():
    # 1️⃣ Tenta variável de ambiente
    key = os.getenv("GOOGLE_MAPS_API_KEY")
    if key:
        return key

    # 2️⃣ Tenta config.json
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            return cfg.get("google_maps_api_key")

    return None

API_KEY = load_api_key()

if not API_KEY:
    raise RuntimeError("Google Maps API Key não configurada")

gmaps = googlemaps.Client(key=API_KEY)

# ======================================================
# FUNÇÕES DE CÁLCULO
# ======================================================

def normalizar(texto):
    if texto is None:
        return ""
    return str(texto).strip().lower()

def calcular_distancia_segura(origem, destino, cache):
    chave = normalizar(destino)

    if not chave:
        return None

    if chave in cache:
        return cache[chave]

    try:
        result = gmaps.distance_matrix(origem, destino)

        element = result["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            return None

        km = element["distance"]["value"] / 1000
        cache[chave] = km
        return km

    except Exception:
        return None

def calcular_pagamentos(df, origem, base, valor_km, minimo, cache):
    entregadores = defaultdict(lambda: {"total": 0, "entregas": 0, "dist": 0})

    for _, row in df.iterrows():
        rua = row.get("Rua")
        numero = row.get("Numero")
        bairro = row.get("Bairro")
        cidade = row.get("Cidade")

        if not rua or not cidade:
            continue

        endereco = f"{rua}, {numero or ''} - {bairro or ''} - {cidade}"

        km = calcular_distancia_segura(origem, endereco, cache)
        if km is None:
            continue

        valor = max(base + km * valor_km, minimo)
        nome = row.get("Entregador", "Desconhecido")

        entregadores[nome]["total"] += valor
        entregadores[nome]["entregas"] += 1
        entregadores[nome]["dist"] += km

    resultado = []
    resumo = []

    for nome, d in entregadores.items():
        if d["entregas"] == 0:
            continue

        media_km = d["dist"] / d["entregas"]

        resultado.append({
            "entregador": nome,
            "total": round(d["total"], 2),
            "entregas": d["entregas"],
            "media_km": round(media_km, 2)
        })

        resumo.append({
            "data": datetime.now().strftime("%Y-%m-%d"),
            "entregador": nome,
            "total": round(d["total"], 2),
            "entregas": d["entregas"],
            "media_km": round(media_km, 2)
        })

    return resultado, resumo
