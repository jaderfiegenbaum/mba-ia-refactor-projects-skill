from src.database import get_db
from src.errors import ConflictError, NotFoundError

STATUS_VALIDOS = ("pendente", "aprovado", "enviado", "entregue", "cancelado")

LIMITE_DESCONTO_ALTO = 10000
LIMITE_DESCONTO_MEDIO = 5000
LIMITE_DESCONTO_BAIXO = 1000
PERCENTUAL_DESCONTO_ALTO = 0.1
PERCENTUAL_DESCONTO_MEDIO = 0.05
PERCENTUAL_DESCONTO_BAIXO = 0.02

_PEDIDOS_QUERY = """
    SELECT p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
           i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
           pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
    {where_clause}
    ORDER BY p.id
"""


def _montar_pedidos(rows):
    pedidos = {}
    for row in rows:
        pedido_id = row["pedido_id"]
        if pedido_id not in pedidos:
            pedidos[pedido_id] = {
                "id": pedido_id,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
        if row["item_id"] is not None:
            pedidos[pedido_id]["itens"].append(
                {
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] or "Desconhecido",
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                }
            )
    return list(pedidos.values())


def criar(usuario_id, itens):
    db = get_db()

    itens_com_produto = []
    total = 0
    for item in itens:
        produto = db.execute(
            "SELECT * FROM produtos WHERE id = ? AND ativo = 1", (item["produto_id"],)
        ).fetchone()
        if produto is None:
            raise NotFoundError(f"Produto {item['produto_id']} não encontrado")
        total += produto["preco"] * item["quantidade"]
        itens_com_produto.append((item, produto))

    with db:
        cursor = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cursor.lastrowid

        for item, produto in itens_com_produto:
            atualizado = db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            )
            if atualizado.rowcount == 0:
                raise ConflictError(f"Estoque insuficiente para o produto \"{produto['nome']}\"")

            db.execute(
                """
                INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
                VALUES (?, ?, ?, ?)
                """,
                (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
            )

    return {"pedido_id": pedido_id, "total": total}


def listar_por_usuario(usuario_id):
    rows = get_db().execute(
        _PEDIDOS_QUERY.format(where_clause="WHERE p.usuario_id = ?"), (usuario_id,)
    ).fetchall()
    return _montar_pedidos(rows)


def listar_todos():
    rows = get_db().execute(_PEDIDOS_QUERY.format(where_clause="")).fetchall()
    return _montar_pedidos(rows)


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    atualizado = db.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)
    )
    db.commit()
    if atualizado.rowcount == 0:
        raise NotFoundError("Pedido não encontrado")


def relatorio_vendas():
    db = get_db()

    total_pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    faturamento = db.execute("SELECT SUM(total) FROM pedidos").fetchone()[0] or 0
    pendentes = db.execute(
        "SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'"
    ).fetchone()[0]
    aprovados = db.execute(
        "SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'"
    ).fetchone()[0]
    cancelados = db.execute(
        "SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'"
    ).fetchone()[0]

    desconto = 0
    if faturamento > LIMITE_DESCONTO_ALTO:
        desconto = faturamento * PERCENTUAL_DESCONTO_ALTO
    elif faturamento > LIMITE_DESCONTO_MEDIO:
        desconto = faturamento * PERCENTUAL_DESCONTO_MEDIO
    elif faturamento > LIMITE_DESCONTO_BAIXO:
        desconto = faturamento * PERCENTUAL_DESCONTO_BAIXO

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
