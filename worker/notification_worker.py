from time import sleep

from services import transaction, notification
from session_factory import create_session
from models import NotificationJob
from services.result import NotificationJobClaim

def processor(
    notification: NotificationJobClaim
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
    worker_id = 5
    lease_seconds = 2
    args = [worker_id, lease_seconds]

    while True:
        claim = transaction.run_transaction_once(
            create_session,
            notification.claim_one_notification_operation,
            args
        )

        if claim is None:
            sleep(1)
            continue

        processor(claim)