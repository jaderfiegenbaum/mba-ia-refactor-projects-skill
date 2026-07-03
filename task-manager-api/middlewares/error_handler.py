import logging

from flask import jsonify

from errors.exceptions import ApiError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify({'error': error.message}), error.status_code

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({'error': 'Recurso não encontrado'}), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception('Erro não tratado')
        return jsonify({'error': 'Erro interno do servidor'}), 500
