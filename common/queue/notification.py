import dataclasses
import json
from typing import Optional

import deserialize
from aioredis import RedisConnection

from common.queue import rpush, blpop
from common.structure.job.notification import NotificationJob


NOTIFICATION_JOB_QUEUE_TOPIC = 'NOTIFICATION_JOB_QUEUE'


async def publish_notification_job(
    redis_conn: RedisConnection,
    job: NotificationJob,
):
    return await rpush(
        redis_conn=redis_conn,
        topic=NOTIFICATION_JOB_QUEUE_TOPIC,
        job=dataclasses.asdict(job),
    )


async def blocking_get_notification_job(
    redis_conn: RedisConnection,
    timeout: int = 0
) -> Optional[NotificationJob]:
    job_json = await blpop(
        redis_conn=redis_conn,
        topic=NOTIFICATION_JOB_QUEUE_TOPIC,
        timeout=timeout
    )
    if not job_json:
        return None

    job = json.loads(job_json)
    return deserialize.deserialize(NotificationJob, job)
