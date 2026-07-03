from werkzeug.security import check_password_hash, generate_password_hash

from src.database import get_db
from src.errors import NotFoundError


def _to_public_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def listar_todos():
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [_to_public_dict(row) for row in rows]


def buscar_por_id(id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (id,)).fetchone()
    return _to_public_dict(row) if row else None


def exigir_por_id(id):
    usuario = buscar_por_id(id)
    if usuario is None:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar(nome, email, senha, tipo="cliente"):
    db = get_db()
    senha_hash = generate_password_hash(senha)
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid


def autenticar(email, senha):
    row = get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row and check_password_hash(row["senha"], senha):
        return _to_public_dict(row)
    return None
