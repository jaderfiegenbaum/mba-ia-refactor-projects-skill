import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-key-change-me")
DB_PATH = os.environ.get("DB_PATH", "loja.db")
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))
