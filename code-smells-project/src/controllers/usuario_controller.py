import logging

from flask import jsonify, request

from src.errors import UnauthorizedError, ValidationError
from src.middlewares.auth import gerar_token
from src.models import usuario_model

logger = logging.getLogger(__name__)


def listar_usuarios():
    usuarios = usuario_model.listar_todos()
    return jsonify({"dados": usuarios, "sucesso": True}), 200


def buscar_usuario(id):
    usuario = usuario_model.exigir_por_id(id)
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    dados = request.get_json()
    if not dados:
        raise ValidationError("Dados inválidos")

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if "@" not in email:
        raise ValidationError("Email inválido")

    id = usuario_model.criar(nome, email, senha)
    logger.info("Usuário criado", extra={"usuario_id": id})
    return jsonify({"dados": {"id": id}, "sucesso": True}), 201


def login():
    dados = request.get_json() or {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")

    usuario = usuario_model.autenticar(email, senha)
    if usuario is None:
        logger.info("Tentativa de login falhou")
        raise UnauthorizedError("Email ou senha inválidos")

    logger.info("Login bem-sucedido", extra={"usuario_id": usuario["id"]})
    token = gerar_token(usuario)
    return jsonify({"dados": usuario, "token": token, "sucesso": True, "mensagem": "Login OK"}), 200
