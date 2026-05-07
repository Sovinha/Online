import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
CACHE_FILE = os.path.join(BASE_DIR, "cache_distancias.json")
HISTORY_FILE = os.path.join(BASE_DIR, "historico.csv")


def load_config():
    config = {}

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Erro ao carregar {CONFIG_FILE}: {e}")

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if api_key:
        config["google_maps_api_key"] = api_key

    return config
