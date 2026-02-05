import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
CACHE_FILE = os.path.join(BASE_DIR, "cache_distancias.json")
HISTORY_FILE = os.path.join(BASE_DIR, "historico.csv")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
import os
import json

# Define a raiz do projeto (sobe dois níveis a partir deste arquivo)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Definição dos caminhos dos arquivos
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
CACHE_FILE = os.path.join(BASE_DIR, "cache_distancias.json")
HISTORY_FILE = os.path.join(BASE_DIR, "historico.csv")

def load_config():
    """Carrega as configurações do projeto de forma segura."""
    if not os.path.exists(CONFIG_FILE):
        return {}
        
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Erro ao carregar {CONFIG_FILE}: {e}")
        return {}