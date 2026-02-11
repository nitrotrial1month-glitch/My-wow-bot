import json
import os

CONFIG_FILE = 'config.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_data = {
            "anti_link": {"enabled": False, "blocked_list": []},
            "bad_words": [],
            "auto_role_id": None,
            "welcome": {"enabled": True, "channel_id": None, "title": "Welcome!", "description": "Hi {member}!", "image_url": None, "color": 0x00ff00},
            "leave": {"channel_id": None, "title": "Goodbye!", "description": "{member} left.", "image_url": None, "color": 0xff0000}
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=4)
        return default_data
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
      
