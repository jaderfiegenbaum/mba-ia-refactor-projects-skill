import logging

from database import db
from errors.exceptions import NotFoundError, ValidationError
from models.category import Category
from models.task import TASK_STATUSES, Task
from models.user import User
from services.notification_service import notification_service
from utils.helpers import calculate_percentage, process_task_data, utc_now

logger = logging.getLogger(__name__)


def list_tasks():
    tasks = Task.list_with_relations()
    result = []
    for task in tasks:
        data = task.to_dict()
        data['user_name'] = task.user.name if task.user else None
        data['category_name'] = task.category.name if task.category else None
        result.append(data)
    return result


def get_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task.to_dict()


def create_task(data):
    if not data:
        raise ValidationError('Dados inválidos')
    if not data.get('title'):
        raise ValidationError('Título é obrigatório')

    processed, error = process_task_data(data)
    if error:
        raise ValidationError(error)

    user_id = data.get('user_id')
    if user_id and not User.query.get(user_id):
        raise NotFoundError('Usuário não encontrado')

    category_id = data.get('category_id')
    if category_id and not Category.query.get(category_id):
        raise NotFoundError('Categoria não encontrada')

    task = Task(
        title=processed['title'],
        description=processed.get('description', data.get('description', '')),
        status=processed.get('status', data.get('status', 'pending')),
        priority=processed.get('priority', data.get('priority', 3)),
        user_id=user_id,
        category_id=category_id,
        due_date=processed.get('due_date'),
        tags=processed.get('tags'),
    )

    db.session.add(task)
    db.session.commit()
    logger.info('Task criada: %s - %s', task.id, task.title)

    if task.user_id:
        user = User.query.get(task.user_id)
        if user:
            notification_service.notify_task_assigned(user, task)

    return task.to_dict()


def update_task(task_id, data):
    task = Task.query.get(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    if not data:
        raise ValidationError('Dados inválidos')

    processed, error = process_task_data(data, existing_task=task)
    if error:
        raise ValidationError(error)

    if 'user_id' in data:
        if data['user_id'] and not User.query.get(data['user_id']):
            raise NotFoundError('Usuário não encontrado')
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id'] and not Category.query.get(data['category_id']):
            raise NotFoundError('Categoria não encontrada')
        task.category_id = data['category_id']

    for field in ('title', 'description', 'status', 'priority', 'due_date', 'tags'):
        if field in processed:
            setattr(task, field, processed[field])

    task.updated_at = utc_now()

    db.session.commit()
    logger.info('Task atualizada: %s', task.id)
    return task.to_dict()


def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')

    db.session.delete(task)
    db.session.commit()
    logger.info('Task deletada: %s', task_id)
    return {'message': 'Task deletada com sucesso'}


def search_tasks(args):
    query = args.get('q', '')
    status = args.get('status', '')
    priority = args.get('priority', '')
    user_id = args.get('user_id', '')

    tasks = Task.query

    if query:
        tasks = tasks.filter(
            db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%'),
            )
        )

    if status:
        tasks = tasks.filter(Task.status == status)

    if priority:
        tasks = tasks.filter(Task.priority == int(priority))

    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))

    return [task.to_dict() for task in tasks.all()]


def task_stats():
    total = Task.query.count()
    status_counts = {
        status: Task.query.filter_by(status=status).count() for status in TASK_STATUSES
    }
    overdue_count = Task.query.filter(
        Task.due_date < utc_now(), Task.status.notin_(['done', 'cancelled'])
    ).count()

    return {
        'total': total,
        'pending': status_counts['pending'],
        'in_progress': status_counts['in_progress'],
        'done': status_counts['done'],
        'cancelled': status_counts['cancelled'],
        'overdue': overdue_count,
        'completion_rate': calculate_percentage(status_counts['done'], total),
    }
