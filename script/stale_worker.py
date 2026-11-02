from sqlmodel import select
from datetime import datetime, timezone
from time import sleep
from threading import Thread

from services import notification, transaction
from services.result import NotificationJobClaim

from session_factory import create_session

from models import NotificationJob

with create_session() as session:
    notification_job = session.exec(
        select(NotificationJob).where(
            NotificationJob.job_type == "test-job"
        )
    ).first()

    if notification_job is not None:
        session.delete(notification_job)
        session.commit()

    notification_job = NotificationJob(
        event_id=1,
        job_type="test-job",
        payload={"type": "test-job"},
        created_at=datetime.now(timezone.utc),
        next_attempt_at=datetime.now(timezone.utc),
    )
    session.add(notification_job)
    session.commit()


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
                claim_version: {notification.claim_version}
        """
    )

def worker_1():
    worker_id = "notification-worker-1"
    lease_seconds = 2
    args = [worker_id, lease_seconds]

    claim = transaction.run_transaction_once(
        create_session,
        notification.claim_one_notification_operation,
        args
    )

    if claim is None:
        print("worker_1: no job claimed!")
        return
    
    sleep(5)

    processor(claim)

    finalize_result = transaction.run_transaction_once(
        create_session,
        notification.finalize_notification_success_operation,
        [claim.id, claim.claim_version]
    )
    print(f"worker_1: finalize_result = {finalize_result}")

def worker_2():
    sleep(2)
    worker_id = "notification-worker-2"
    lease_seconds = 2
    args = [worker_id, lease_seconds]

    claim = transaction.run_transaction_once(
        create_session,
        notification.claim_one_notification_operation,
        args
    )

    if claim is None:
        print("worker_2: no job claimed!")
        return

    sleep(5)

    processor(claim)

    finalize_result = transaction.run_transaction_once(
        create_session,
        notification.finalize_notification_success_operation,
        [claim.id, claim.claim_version]
    )
    print(f"worker_2: finalize_result = {finalize_result}")

t1 = Thread(
    target=worker_1
)
t2 = Thread(
    target=worker_2
)

t1.start()
t2.start()

t1.join()
t2.join()

with create_session() as session:
    notification = session.exec(
        select(NotificationJob).where(
            NotificationJob.job_type == "test-job"
        )
    ).first()

    assert notification is not None

    print(
        f"""
        After Notification Info:
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
            claim_version: {notification.claim_version}
        """
    )

    session.delete(notification)
    session.commit()


# 以上运行输出
# uv run python -m script.stale_worker
# 2026-11-02 15:22:07,892 INFO sqlalchemy.engine.Engine select pg_catalog.version()
# 2026-11-02 15:22:07,893 INFO sqlalchemy.engine.Engine [raw sql] {}
# 2026-11-02 15:22:07,897 INFO sqlalchemy.engine.Engine select current_schema()
# 2026-11-02 15:22:07,897 INFO sqlalchemy.engine.Engine [raw sql] {}
# 2026-11-02 15:22:07,901 INFO sqlalchemy.engine.Engine show standard_conforming_strings
# 2026-11-02 15:22:07,901 INFO sqlalchemy.engine.Engine [raw sql] {}
# 2026-11-02 15:22:07,906 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-11-02 15:22:07,929 INFO sqlalchemy.engine.Engine SELECT notification_jobs.id, notification_jobs.event_id, notification_jobs.job_type, notification_jobs.payload, notification_jobs.created_at, notification_jobs.processed_at, notification_jobs.retry_count, notification_jobs.next_attempt_at, notification_jobs.last_error, notification_jobs.failed_at, notification_jobs.lease_until, notification_jobs.claimed_by, notification_jobs.claim_version 
# FROM notification_jobs 
# WHERE notification_jobs.job_type = %(job_type_1)s::VARCHAR
# 2026-11-02 15:22:07,930 INFO sqlalchemy.engine.Engine [generated in 0.00072s] {'job_type_1': 'test-job'}
# 2026-11-02 15:22:07,942 INFO sqlalchemy.engine.Engine INSERT INTO notification_jobs (event_id, job_type, payload, created_at, processed_at, retry_count, next_attempt_at, last_error, failed_at, lease_until, claimed_by, claim_version) VALUES (%(event_id)s::INTEGER, %(job_type)s::VARCHAR, %(payload)s::JSONB, %(created_at)s::TIMESTAMP WITH TIME ZONE, %(processed_at)s::TIMESTAMP WITH TIME ZONE, %(retry_count)s::INTEGER, %(next_attempt_at)s::TIMESTAMP WITH TIME ZONE, %(last_error)s::VARCHAR, %(failed_at)s::TIMESTAMP WITH TIME ZONE, %(lease_until)s::TIMESTAMP WITH TIME ZONE, %(claimed_by)s::VARCHAR, %(claim_version)s::INTEGER) RETURNING notification_jobs.id
# 2026-11-02 15:22:07,942 INFO sqlalchemy.engine.Engine [generated in 0.00052s] {'event_id': 1, 'job_type': 'test-job', 'payload': Jsonb({'type': 'test-job'}), 'created_at': datetime.datetime(2026, 11, 2, 7, 22, 7, 938376, tzinfo=datetime.timezone.utc), 'processed_at': None, 'retry_count': 0, 'next_attempt_at': datetime.datetime(2026, 11, 2, 7, 22, 7, 938382, tzinfo=datetime.timezone.utc), 'last_error': None, 'failed_at': None, 'lease_until': None, 'claimed_by': None, 'claim_version': 0}
# 2026-11-02 15:22:07,946 INFO sqlalchemy.engine.Engine COMMIT
# 2026-11-02 15:22:07,948 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-11-02 15:22:07,952 INFO sqlalchemy.engine.Engine SELECT notification_jobs.id, notification_jobs.event_id, notification_jobs.job_type, notification_jobs.payload, notification_jobs.created_at, notification_jobs.processed_at, notification_jobs.retry_count, notification_jobs.next_attempt_at, notification_jobs.last_error, notification_jobs.failed_at, notification_jobs.lease_until, notification_jobs.claimed_by, notification_jobs.claim_version 
# FROM notification_jobs 
# WHERE notification_jobs.processed_at IS NULL AND notification_jobs.failed_at IS NULL AND notification_jobs.next_attempt_at <= now() AND (notification_jobs.lease_until IS NULL OR notification_jobs.lease_until <= now()) ORDER BY notification_jobs.id 
#  LIMIT %(param_1)s::INTEGER FOR UPDATE SKIP LOCKED
# 2026-11-02 15:22:07,952 INFO sqlalchemy.engine.Engine [generated in 0.00037s] {'param_1': 1}
# 2026-11-02 15:22:07,958 INFO sqlalchemy.engine.Engine UPDATE notification_jobs SET lease_until=%(lease_until)s::TIMESTAMP WITH TIME ZONE, claimed_by=%(claimed_by)s::VARCHAR, claim_version=%(claim_version)s::INTEGER WHERE notification_jobs.id = %(notification_jobs_id)s::INTEGER
# 2026-11-02 15:22:07,958 INFO sqlalchemy.engine.Engine [generated in 0.00039s] {'lease_until': datetime.datetime(2026, 11, 2, 7, 22, 9, 955920, tzinfo=datetime.timezone.utc), 'claimed_by': 'notification-worker-1', 'claim_version': 1, 'notification_jobs_id': 5}
# 2026-11-02 15:22:07,960 INFO sqlalchemy.engine.Engine COMMIT
# 2026-11-02 15:22:09,959 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-11-02 15:22:09,960 INFO sqlalchemy.engine.Engine SELECT notification_jobs.id, notification_jobs.event_id, notification_jobs.job_type, notification_jobs.payload, notification_jobs.created_at, notification_jobs.processed_at, notification_jobs.retry_count, notification_jobs.next_attempt_at, notification_jobs.last_error, notification_jobs.failed_at, notification_jobs.lease_until, notification_jobs.claimed_by, notification_jobs.claim_version 
# FROM notification_jobs 
# WHERE notification_jobs.processed_at IS NULL AND notification_jobs.failed_at IS NULL AND notification_jobs.next_attempt_at <= now() AND (notification_jobs.lease_until IS NULL OR notification_jobs.lease_until <= now()) ORDER BY notification_jobs.id 
#  LIMIT %(param_1)s::INTEGER FOR UPDATE SKIP LOCKED
# 2026-11-02 15:22:09,960 INFO sqlalchemy.engine.Engine [cached since 2.009s ago] {'param_1': 1}
# 2026-11-02 15:22:09,964 INFO sqlalchemy.engine.Engine UPDATE notification_jobs SET lease_until=%(lease_until)s::TIMESTAMP WITH TIME ZONE, claimed_by=%(claimed_by)s::VARCHAR, claim_version=%(claim_version)s::INTEGER WHERE notification_jobs.id = %(notification_jobs_id)s::INTEGER
# 2026-11-02 15:22:09,964 INFO sqlalchemy.engine.Engine [cached since 2.006s ago] {'lease_until': datetime.datetime(2026, 11, 2, 7, 22, 11, 963360, tzinfo=datetime.timezone.utc), 'claimed_by': 'notification-worker-2', 'claim_version': 2, 'notification_jobs_id': 5}
# 2026-11-02 15:22:09,965 INFO sqlalchemy.engine.Engine COMMIT

#         Notification Process:
#             Notification Info:
#                 id: 5
#                 event_id: 1
#                 job_type: test-job
#                 payload: {'type': 'test-job'}
#                 created_at: 2026-11-02 07:22:07.938376+00:00
#                 processed_at: None
#                 retry_count: 0
#                 next_attempt_at: 2026-11-02 07:22:07.938382+00:00
#                 last_error: None
#                 failed_at: None
#                 claim_version: 1
        
# 2026-11-02 15:22:12,965 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-11-02 15:22:12,969 INFO sqlalchemy.engine.Engine UPDATE notification_jobs SET processed_at=now(), lease_until=%(lease_until)s::TIMESTAMP WITH TIME ZONE, claimed_by=%(claimed_by)s::VARCHAR WHERE notification_jobs.id = %(id_1)s::INTEGER AND notification_jobs.claim_version = %(claim_version_1)s::INTEGER AND notification_jobs.processed_at IS NULL AND notification_jobs.failed_at IS NULL RETURNING notification_jobs.id
# 2026-11-02 15:22:12,969 INFO sqlalchemy.engine.Engine [generated in 0.00042s] {'lease_until': None, 'claimed_by': None, 'id_1': 5, 'claim_version_1': 1}
# 2026-11-02 15:22:12,973 INFO sqlalchemy.engine.Engine COMMIT
# worker_1: finalize_result = stale_claim

#         Notification Process:
#             Notification Info:
#                 id: 5
#                 event_id: 1
#                 job_type: test-job
#                 payload: {'type': 'test-job'}
#                 created_at: 2026-11-02 07:22:07.938376+00:00
#                 processed_at: None
#                 retry_count: 0
#                 next_attempt_at: 2026-11-02 07:22:07.938382+00:00
#                 last_error: None
#                 failed_at: None
#                 claim_version: 2
        
# 2026-11-02 15:22:14,982 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-11-02 15:22:14,983 INFO sqlalchemy.engine.Engine UPDATE notification_jobs SET processed_at=now(), lease_until=%(lease_until)s::TIMESTAMP WITH TIME ZONE, claimed_by=%(claimed_by)s::VARCHAR WHERE notification_jobs.id = %(id_1)s::INTEGER AND notification_jobs.claim_version = %(claim_version_1)s::INTEGER AND notification_jobs.processed_at IS NULL AND notification_jobs.failed_at IS NULL RETURNING notification_jobs.id
# 2026-11-02 15:22:14,983 INFO sqlalchemy.engine.Engine [cached since 2.014s ago] {'lease_until': None, 'claimed_by': None, 'id_1': 5, 'claim_version_1': 2}
# 2026-11-02 15:22:14,986 INFO sqlalchemy.engine.Engine COMMIT
# worker_2: finalize_result = processed
# 2026-11-02 15:22:14,989 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-11-02 15:22:14,989 INFO sqlalchemy.engine.Engine SELECT notification_jobs.id, notification_jobs.event_id, notification_jobs.job_type, notification_jobs.payload, notification_jobs.created_at, notification_jobs.processed_at, notification_jobs.retry_count, notification_jobs.next_attempt_at, notification_jobs.last_error, notification_jobs.failed_at, notification_jobs.lease_until, notification_jobs.claimed_by, notification_jobs.claim_version 
# FROM notification_jobs 
# WHERE notification_jobs.job_type = %(job_type_1)s::VARCHAR
# 2026-11-02 15:22:14,989 INFO sqlalchemy.engine.Engine [cached since 7.06s ago] {'job_type_1': 'test-job'}

#         After Notification Info:
#             id: 5
#             event_id: 1
#             job_type: test-job
#             payload: {'type': 'test-job'}
#             created_at: 2026-11-02 07:22:07.938376+00:00
#             processed_at: 2026-11-02 07:22:14.984071+00:00
#             retry_count: 0
#             next_attempt_at: 2026-11-02 07:22:07.938382+00:00
#             last_error: None
#             failed_at: None
#             claim_version: 2
        
# 2026-11-02 15:22:14,993 INFO sqlalchemy.engine.Engine DELETE FROM notification_jobs WHERE notification_jobs.id = %(id)s::INTEGER
# 2026-11-02 15:22:14,993 INFO sqlalchemy.engine.Engine [generated in 0.00035s] {'id': 5}
# 2026-11-02 15:22:14,994 INFO sqlalchemy.engine.Engine COMMIT