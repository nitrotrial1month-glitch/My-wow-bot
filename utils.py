import json
import os
import datetime

CONFIG_FILE = 'config.json'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_data = {
            "anti_link": {"enabled": False, "blocked_list": []},
            "bad_words": [],
            "auto_role_id": None,
            "welcome": {"enabled": True, "channel_id": None, "title": "Welcome!", "description": "Hi {member}!", "image_url": None, "color": 0x00ff00},
            "leave": {"channel_id": None, "title": "Goodbye!", "description": "{member} left.", "image_url": None, "color": 0xff0000},
            "premium": {} # প্রিমিয়াম ইউজারদের ডাটা এখানে থাকবে
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

# --- নতুন প্রিমিয়াম ফাংশনগুলো নিচে ---

def is_user_premium(user_id):
    """চেক করে ইউজারের প্রিমিয়াম মেয়াদ আছে কি না"""
    config = load_config()
    premium_data = config.get("premium", {})
    user_id_str = str(user_id)
    
    if user_id_str in premium_data:
        expiry_date_str = premium_data[user_id_str]
        expiry_date = datetime.datetime.fromisoformat(expiry_date_str)
        
        # বর্তমান সময়ের সাথে মেয়াদ তুলনা
        if datetime.datetime.now() < expiry_date:
            return True
        else:
            # মেয়াদ শেষ হলে রিমুভ করে দেওয়া
            del config["premium"][user_id_str]
            save_config(config)
            return False
    return False

def add_premium(user_id, days):
    """ইউজারকে নির্দিষ্ট দিনের জন্য প্রিমিয়াম দেওয়া"""
    config = load_config()
    if "premium" not in config: config["premium"] = {}
    
    expiry_date = datetime.datetime.now() + datetime.timedelta(days=days)
    config["premium"][str(user_id)] = expiry_date.isoformat()
    save_config(config)
    return expiry_date
