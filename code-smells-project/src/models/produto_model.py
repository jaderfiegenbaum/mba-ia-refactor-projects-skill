from src.database import get_db
from src.errors import NotFoundError

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
NOME_MIN_LENGTH = 2
NOME_MAX_LENGTH = 200


def _to_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def listar_todos():
    rows = get_db().execute("SELECT * FROM produtos WHERE ativo = 1").fetchall()
    return [_to_dict(row) for row in rows]


def buscar_por_id(id):
    row = get_db().execute(
        "SELECT * FROM produtos WHERE id = ? AND ativo = 1", (id,)
    ).fetchone()
    return _to_dict(row) if row else None


def criar(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def atualizar(id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    db.execute(
        """
        UPDATE produtos
        SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ?
        WHERE id = ?
        """,
        (nome, descricao, preco, estoque, categoria, id),
    )
    db.commit()


def deletar(id):
    db = get_db()
    db.execute("UPDATE produtos SET ativo = 0 WHERE id = ?", (id,))
    db.commit()


def buscar(termo, categoria=None, preco_min=None, preco_max=None):
    query = "SELECT * FROM produtos WHERE ativo = 1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        curinga = f"%{termo}%"
        params.extend([curinga, curinga])
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)

    rows = get_db().execute(query, params).fetchall()
    return [_to_dict(row) for row in rows]


def exigir_por_id(id):
    produto = buscar_por_id(id)
    if produto is None:
        raise NotFoundError("Produto não encontrado")
    return produto
