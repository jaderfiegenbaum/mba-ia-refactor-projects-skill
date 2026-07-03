import datetime as dt
import logging

import jwt

from config.settings import SECRET_KEY
from database import db
from errors.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from models.task import Task
from models.user import User
from utils.helpers import MIN_PASSWORD_LENGTH, VALID_ROLES, validate_email

logger = logging.getLogger(__name__)

TOKEN_TTL_HOURS = 8


def list_users():
    return [
        {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'active': user.active,
            'created_at': str(user.created_at),
            'task_count': len(user.tasks),
        }
        for user in User.query.all()
    ]


def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in Task.query.filter_by(user_id=user_id).all()]
    return data


def create_user(data):
    if not data:
        raise ValidationError('Dados inválidos')

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    # Auto-cadastro sempre cria um usuário comum; promoção a admin/manager
    # exige um PUT autenticado por um administrador (ver update_user).
    role = 'user'

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    if not validate_email(email):
        raise ValidationError('Email inválido')
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')
    if User.query.filter_by(email=email).first():
        raise ConflictError('Email já cadastrado')

    user = User(name=name, email=email, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    logger.info('Usuário criado: %s - %s', user.id, user.name)
    return user.to_dict()


def update_user(user_id, data, caller):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    if not data:
        raise ValidationError('Dados inválidos')

    if 'name' in data:
        user.name = data['name']

    if 'email' in data:
        if not validate_email(data['email']):
            raise ValidationError('Email inválido')
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            raise ConflictError('Email já cadastrado')
        user.email = data['email']

    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        user.set_password(data['password'])

    if 'role' in data:
        if not caller.is_admin():
            raise ForbiddenError('Apenas administradores podem alterar o papel de um usuário')
        if data['role'] not in VALID_ROLES:
            raise ValidationError('Role inválido')
        user.role = data['role']

    if 'active' in data:
        user.active = data['active']

    db.session.commit()
    return user.to_dict()


def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    Task.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    logger.info('Usuário deletado: %s', user_id)
    return {'message': 'Usuário deletado com sucesso'}


def get_user_tasks(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    return [task.to_dict() for task in Task.query.filter_by(user_id=user_id).all()]


def login(data):
    if not data:
        raise ValidationError('Dados inválidos')

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise UnauthorizedError('Credenciais inválidas')

    if not user.active:
        raise ForbiddenError('Usuário inativo')

    payload = {
        'user_id': user.id,
        'role': user.role,
        'exp': dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=TOKEN_TTL_HOURS),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': token,
    }
