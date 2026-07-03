from datetime import timedelta

from sqlalchemy import case, func

from database import db
from errors.exceptions import NotFoundError
from models.category import Category
from models.task import TASK_STATUSES, Task
from models.user import User
from utils.helpers import calculate_percentage, utc_now

PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}


def summary_report():
    now = utc_now()

    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    status_counts = dict(db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all())
    priority_counts = dict(db.session.query(Task.priority, func.count(Task.id)).group_by(Task.priority).all())

    overdue_tasks = Task.query.filter(
        Task.due_date < now, Task.status.notin_(['done', 'cancelled'])
    ).all()
    overdue_list = [
        {
            'id': task.id,
            'title': task.title,
            'due_date': str(task.due_date),
            'days_overdue': (now - task.due_date).days,
        }
        for task in overdue_tasks
    ]

    seven_days_ago = now - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()
    recent_done = Task.query.filter(
        Task.status == 'done', Task.updated_at >= seven_days_ago
    ).count()

    productivity_rows = (
        db.session.query(
            User.id,
            User.name,
            func.count(Task.id),
            func.sum(case((Task.status == 'done', 1), else_=0)),
        )
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
        .all()
    )

    user_stats = []
    for user_id, user_name, total, completed in productivity_rows:
        completed = completed or 0
        user_stats.append({
            'user_id': user_id,
            'user_name': user_name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total),
        })

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {status: status_counts.get(status, 0) for status in TASK_STATUSES},
        'tasks_by_priority': {
            label: priority_counts.get(priority, 0) for priority, label in PRIORITY_LABELS.items()
        },
        'overdue': {
            'count': len(overdue_list),
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }


def user_report(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    tasks = Task.query.filter_by(user_id=user_id).all()
    total = len(tasks)
    status_counts = {status: 0 for status in TASK_STATUSES}
    overdue = 0
    high_priority = 0

    for task in tasks:
        if task.status in status_counts:
            status_counts[task.status] += 1
        if task.priority <= 2:
            high_priority += 1
        if task.is_overdue():
            overdue += 1

    return {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': status_counts['done'],
            'pending': status_counts['pending'],
            'in_progress': status_counts['in_progress'],
            'cancelled': status_counts['cancelled'],
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': calculate_percentage(status_counts['done'], total),
        },
    }
