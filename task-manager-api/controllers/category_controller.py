from sqlalchemy import func

from database import db
from errors.exceptions import NotFoundError, ValidationError
from models.category import DEFAULT_COLOR, Category
from models.task import Task


def list_categories():
    counts = dict(
        db.session.query(Task.category_id, func.count(Task.id)).group_by(Task.category_id).all()
    )

    result = []
    for category in Category.query.all():
        data = category.to_dict()
        data['task_count'] = counts.get(category.id, 0)
        result.append(data)
    return result


def create_category(data):
    if not data:
        raise ValidationError('Dados inválidos')

    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')

    category = Category(
        name=name,
        description=data.get('description', ''),
        color=data.get('color', DEFAULT_COLOR),
    )

    db.session.add(category)
    db.session.commit()
    return category.to_dict()


def update_category(cat_id, data):
    category = Category.query.get(cat_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    if not data:
        raise ValidationError('Dados inválidos')

    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = data['color']

    db.session.commit()
    return category.to_dict()


def delete_category(cat_id):
    category = Category.query.get(cat_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')

    Task.query.filter_by(category_id=cat_id).update({'category_id': None})
    db.session.delete(category)
    db.session.commit()
    return {'message': 'Categoria deletada'}
