import json
import os
import datetime

CONFIG_FILE = 'config.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_data = {
            "anti_link": {"enabled": False, "blocked_list": [], "bypass_roles": [], "blocked_keywords": []},
            "bad_words": [],
            "auto_role_id": None,
            "welcome": {"enabled": True, "channel_id": None, "title": "Welcome!", "description": "Hi {member}!", "image_url": None, "color": 0x00ff00},
            "leave": {"channel_id": None, "title": "Goodbye!", "description": "{member} left.", "image_url": None, "color": 0xff0000},
            "premium": {} 
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=4)
        return default_data
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        try: 
            data = json.load(f)
            # নিশ্চিত করা হচ্ছে যেন 'premium' কি-টি সব সময় থাকে [cite: 2026-02-09]
            if "premium" not in data:
                data["premium"] = {}
            return data
        except: 
            return {"premium": {}} # এরর হলেও যেন প্রিমিয়াম চেক না আটকায়

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def is_user_premium(user_id):
    config = load_config()
    premium_data = config.get("premium", {})
    user_id_str = str(user_id) # আইডি স্ট্রিং হিসেবে চেক করা নিরাপদ
    
    if user_id_str in premium_data:
        try:
            expiry_date_str = premium_data[user_id_str]
            expiry_date = datetime.datetime.fromisoformat(expiry_date_str)
            
            if datetime.datetime.now() < expiry_date:
                return True
            else:
                # মেয়াদ শেষ হলে অটো ডিলিট [cite: 2026-02-09]
                del config["premium"][user_id_str]
                save_config(config)
                return False
        except Exception:
            return False
    return False

def add_premium(user_id, days):
    config = load_config()
    if "premium" not in config: config["premium"] = {}
    
    expiry_date = datetime.datetime.now() + datetime.timedelta(days=days)
    config["premium"][str(user_id)] = expiry_date.isoformat()
    save_config(config)
    return expiry_date
