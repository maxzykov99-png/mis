import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UI_DIR = os.path.join(BASE_DIR, "ui")
DB_PATH = os.path.join(BASE_DIR, "app.db")
SETTINGS_FILE = os.path.join(BASE_DIR, "app_settings.json")

DEFAULT_AUTOSAVE_INTERVAL = 60
