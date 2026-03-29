import os, json
from .models import Settings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

def get_cfg() -> Settings:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Settings(**data)
        except Exception as e:
            print(f"Ошибка загрузки config.json: {e}")
    return Settings()

def save_cfg(s: Settings):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(s.model_dump(), f, indent=2, ensure_ascii=False)