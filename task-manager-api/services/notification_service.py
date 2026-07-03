import logging
import smtplib

from config.settings import SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER
from utils.helpers import utc_now

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.notifications = []

    def send_email(self, to, subject, body):
        if not SMTP_USER or not SMTP_PASSWORD:
            logger.info('SMTP não configurado, pulando envio de email para %s', to)
            return False

        try:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(SMTP_USER, to, message)
            server.quit()
            logger.info('Email enviado para %s', to)
            return True
        except Exception:
            logger.exception('Erro ao enviar email para %s', to)
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': utc_now(),
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]


notification_service = NotificationService()
