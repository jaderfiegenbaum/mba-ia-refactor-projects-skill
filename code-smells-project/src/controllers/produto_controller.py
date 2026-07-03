import logging

from flask import jsonify, request

from src.errors import ValidationError
from src.models import produto_model

logger = logging.getLogger(__name__)


def _validar_dados(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    for campo in ("nome", "preco", "estoque"):
        if campo not in dados:
            raise ValidationError(f"{campo.capitalize()} é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", "geral")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < produto_model.NOME_MIN_LENGTH:
        raise ValidationError("Nome muito curto")
    if len(nome) > produto_model.NOME_MAX_LENGTH:
        raise ValidationError("Nome muito longo")
    if categoria not in produto_model.CATEGORIAS_VALIDAS:
        raise ValidationError(
            "Categoria inválida. Válidas: " + str(produto_model.CATEGORIAS_VALIDAS)
        )

    return nome, descricao, preco, estoque, categoria


def listar_produtos():
    produtos = produto_model.listar_todos()
    logger.info("Listando produtos", extra={"total": len(produtos)})
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id):
    produto = produto_model.exigir_por_id(id)
    return jsonify({"dados": produto, "sucesso": True}), 200


def criar_produto():
    dados = request.get_json()
    nome, descricao, preco, estoque, categoria = _validar_dados(dados)

    id = produto_model.criar(nome, descricao, preco, estoque, categoria)
    logger.info("Produto criado", extra={"produto_id": id})
    return jsonify({"dados": {"id": id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    produto_model.exigir_por_id(id)
    dados = request.get_json()
    nome, descricao, preco, estoque, categoria = _validar_dados(dados)

    produto_model.atualizar(id, nome, descricao, preco, estoque, categoria)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    produto_model.exigir_por_id(id)
    produto_model.deletar(id)
    logger.info("Produto deletado", extra={"produto_id": id})
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)

    preco_min = float(preco_min) if preco_min else None
    preco_max = float(preco_max) if preco_max else None

    resultados = produto_model.buscar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
