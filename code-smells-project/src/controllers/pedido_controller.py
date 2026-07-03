import logging

from flask import jsonify, request

from src.errors import ValidationError
from src.models import pedido_model

logger = logging.getLogger(__name__)


def _validar_itens(itens):
    for item in itens:
        if "produto_id" not in item or "quantidade" not in item:
            raise ValidationError("Cada item precisa de produto_id e quantidade")
        if not isinstance(item["produto_id"], int) or isinstance(item["produto_id"], bool):
            raise ValidationError("produto_id deve ser um número inteiro")
        quantidade = item["quantidade"]
        if isinstance(quantidade, bool) or not isinstance(quantidade, (int, float)) or quantidade <= 0:
            raise ValidationError("Quantidade deve ser um número positivo")


def criar_pedido():
    dados = request.get_json()
    if not dados:
        raise ValidationError("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    _validar_itens(itens)

    resultado = pedido_model.criar(usuario_id, itens)

    logger.info(
        "Notificações de novo pedido disparadas",
        extra={"pedido_id": resultado["pedido_id"], "usuario_id": usuario_id},
    )

    return jsonify(
        {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}
    ), 201


def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_model.listar_por_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos_pedidos():
    pedidos = pedido_model.listar_todos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = request.get_json() or {}
    novo_status = dados.get("status", "")

    if novo_status not in pedido_model.STATUS_VALIDOS:
        raise ValidationError("Status inválido")

    pedido_model.atualizar_status(pedido_id, novo_status)

    if novo_status == "aprovado":
        logger.info("Pedido aprovado, preparar envio", extra={"pedido_id": pedido_id})
    if novo_status == "cancelado":
        logger.info("Pedido cancelado, devolver estoque", extra={"pedido_id": pedido_id})

    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
