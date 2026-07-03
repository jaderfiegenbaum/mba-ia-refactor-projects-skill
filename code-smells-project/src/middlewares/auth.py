from functools import wraps

from flask import g, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from src.config.settings import SECRET_KEY
from src.errors import ForbiddenError, UnauthorizedError

TOKEN_MAX_AGE_SECONDS = 8 * 60 * 60

_serializer = URLSafeTimedSerializer(SECRET_KEY)


def gerar_token(usuario):
    return _serializer.dumps({"id": usuario["id"], "tipo": usuario["tipo"]})


def _usuario_do_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[len("Bearer "):]
    try:
        return _serializer.loads(token, max_age=TOKEN_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        usuario = _usuario_do_token()
        if usuario is None:
            raise UnauthorizedError("Autenticação necessária")
        g.usuario_atual = usuario
        return fn(*args, **kwargs)

    return wrapper


def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        usuario = _usuario_do_token()
        if usuario is None:
            raise UnauthorizedError("Autenticação necessária")
        if usuario.get("tipo") != "admin":
            raise ForbiddenError("Acesso restrito a administradores")
        g.usuario_atual = usuario
        return fn(*args, **kwargs)

    return wrapper


def require_owner_or_admin(usuario_id_param):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            usuario = _usuario_do_token()
            if usuario is None:
                raise UnauthorizedError("Autenticação necessária")
            alvo = kwargs.get(usuario_id_param)
            if usuario.get("tipo") != "admin" and usuario.get("id") != alvo:
                raise ForbiddenError("Acesso não autorizado a este recurso")
            g.usuario_atual = usuario
            return fn(*args, **kwargs)

        return wrapper

    return decorator
