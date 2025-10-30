
import json, os, hashlib
from config import SETTINGS_FILE, DEFAULT_AUTOSAVE_INTERVAL

DEFAULTS = {
    "autosave_on": True,
    "autosave_interval": DEFAULT_AUTOSAVE_INTERVAL,
    "current_user": None,
    "organisations": [],
    "medics": [],
    "users": {},
    "theme": "light"
}

def _hash(pw: str):
    return hashlib.sha256(pw.encode('utf-8')).hexdigest()

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        s = DEFAULTS.copy()
        s['users'] = {'admin': _hash('admin')}
        save_settings(s)
        return s
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            s = json.load(f)
        # ensure defaults
        for k, v in DEFAULTS.items():
            if k not in s:
                s[k] = v
        return s
    except Exception:
        s = DEFAULTS.copy()
        s['users'] = {'admin': _hash('admin')}
        save_settings(s)
        return s

def save_settings(s: dict):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print('Не удалось сохранить настройки:', e)

def verify_user(username: str, password: str) -> bool:
    s = load_settings()
    users = s.get('users', {})
    if username not in users:
        return False
    return users.get(username) == _hash(password)

def add_user(username: str, password: str):
    s = load_settings()
    users = s.get('users', {})
    users[username] = _hash(password)
    s['users'] = users
    save_settings(s)

def change_password(username: str, old_password: str, new_password: str) -> bool:
    if not verify_user(username, old_password):
        return False
    s = load_settings()
    users = s.get('users', {})
    users[username] = _hash(new_password)
    s['users'] = users
    save_settings(s)
    return True

def set_current_user(username: str):
    s = load_settings()
    s['current_user'] = username
    save_settings(s)

def get_current_user():
    return load_settings().get('current_user')
