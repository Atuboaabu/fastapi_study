from time import sleep

from services import transaction, notification
from session_factory import create_session
from models import NotificationJob
from services.result import NotificationJobClaim
from exceptions import RetryableNotificationException, PermanentNotificationException

from logging_config import configure_logging
import logging

logger = logging.getLogger(__name__)

def processor(
    notification: NotificationJobClaim
):
    logger.info(
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
    configure_logging()
    
    worker_id = "notification-worker-5"
    lease_seconds = 2
    max_attempts = 5
    base_delay_seconds = 2
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
        try:
            processor(claim)
        except RetryableNotificationException as exc:
            error_msg = str(exc)[:500]
            logger.warning(
                "notification retry scheduled: "
                "job_id = %s, "
                "claim_version = %s, "
                "error_msg = %s",
                claim.id,
                claim.claim_version,
                error_msg
            )

            result = transaction.run_transaction_once(
                create_session,
                notification.finalize_notification_retry_operation,
                [
                    claim.id,
                    claim.claim_version,
                    error_msg,
                    max_attempts,
                    base_delay_seconds,
                ]
            )
        except PermanentNotificationException as exc:
            error_msg = str(exc)[:500]
            logger.error(
                "notification failed: "
                "job_id = %s, "
                "claim_version = %s, "
                "error_msg = %s",
                claim.id,
                claim.claim_version,
                error_msg
            )

            result = transaction.run_transaction_once(
                create_session,
                notification.finalize_notification_permanent_operation,
                [
                    claim.id,
                    claim.claim_version,
                    error_msg,
                ]
            )
        else:
            result = transaction.run_transaction_once(
                create_session,
                notification.finalize_notification_success_operation,
                [
                    claim.id,
                    claim.claim_version,
                ]
            )
        
        if result == "processed":
            logger.info(
                "notification processed: "
                "job_id = %s, "
                "claim_version = %s",
                claim.id,
                claim.claim_version
            )
        elif result == "stale_claim":
            logger.warning(
                "notification stale claim: "
                "job_id = %s, "
                "claim_version = %s",
                claim.id,
                claim.claim_version
            )