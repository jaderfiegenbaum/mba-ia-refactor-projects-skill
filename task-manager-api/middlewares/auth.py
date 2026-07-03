from functools import wraps

import jwt
from flask import g, request

from config.settings import SECRET_KEY
from errors.exceptions import ForbiddenError, UnauthorizedError
from models.user import User


def _decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except jwt.PyJWTError:
        raise UnauthorizedError('Token inválido ou expirado')


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            raise UnauthorizedError('Token de autenticação ausente')

        token = auth_header.split(' ', 1)[1]
        payload = _decode_token(token)

        user = User.query.get(payload.get('user_id'))
        if not user or not user.active:
            raise UnauthorizedError('Usuário inválido ou inativo')

        g.current_user = user
        return fn(*args, **kwargs)

    return wrapper


def require_admin(fn):
    @require_auth
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not g.current_user.is_admin():
            raise ForbiddenError('Acesso restrito a administradores')
        return fn(*args, **kwargs)

    return wrapper
