from sqlmodel import select, func
from time import sleep

from services import transaction, notification
from session_factory import create_session
from models import NotificationJob

def processor(
    notification: NotificationJob
):
    print(
        f"""
        Notification Process:
            Notification Info:
                id: {notification.id}
                event_id: {notification.event_id}
                job_type: {notification.job_type}
                payload: {notification.payload}
                created_at: {notification.created_at}
                processed_at: {notification.processed_at}
                retry_count: {notification.retry_count}
                next_attempt_at: {notification.next_attempt_at}
                last_error: {notification.last_error}
                failed_at: {notification.failed_at}
        """
    )

def notification_worker_loop():
    running = True
    max_attempts = 5
    base_delay_seconds = 2
    args = [processor, max_attempts, base_delay_seconds]
    session = create_session()

    while running:
        job_count = session.exec(
            select(func.count())
            .select_from(NotificationJob)
            .where(
                NotificationJob.processed_at.is_(None),
                NotificationJob.failed_at.is_(None),
                NotificationJob.next_attempt_at <= func.now()
            )
        ).one()
        if job_count > 0:
            transaction.run_transaction_once(
                create_session,
                notification.process_one_notification_operation,
                args
            )
        else:
            sleep(1)

    session.close()