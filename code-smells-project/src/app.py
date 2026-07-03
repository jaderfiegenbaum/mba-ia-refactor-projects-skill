import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import DEBUG, SECRET_KEY
from src.database import get_db
from src.logging_config import configure_logging
from src.middlewares.error_handler import register_error_handlers
from src.routes.routes import register_routes


def create_app():
    configure_logging()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["DEBUG"] = DEBUG
    CORS(app)

    get_db()
    register_routes(app)
    register_error_handlers(app)

    logging.getLogger(__name__).info("Aplicação inicializada")
    return app
