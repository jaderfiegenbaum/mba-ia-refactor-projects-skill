from flask import Blueprint, jsonify, request

from controllers import category_controller, report_controller
from middlewares.auth import require_auth

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
@require_auth
def summary_report():
    return jsonify(report_controller.summary_report()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
@require_auth
def user_report(user_id):
    return jsonify(report_controller.user_report(user_id)), 200


@report_bp.route('/categories', methods=['GET'])
@require_auth
def get_categories():
    return jsonify(category_controller.list_categories()), 200


@report_bp.route('/categories', methods=['POST'])
@require_auth
def create_category():
    return jsonify(category_controller.create_category(request.get_json())), 201


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@require_auth
def update_category(cat_id):
    return jsonify(category_controller.update_category(cat_id, request.get_json())), 200


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@require_auth
def delete_category(cat_id):
    return jsonify(category_controller.delete_category(cat_id)), 200
