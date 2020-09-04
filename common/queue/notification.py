import dataclasses
import enum
import json
from typing import Optional

import deserialize
from aioredis import RedisConnection

from common.queue import zadd, bzpopmin
from common.structure.job.notification import NotificationJob


class NotificationPriority(enum.IntEnum):
    IMMEDIATE = 0
    SCHEDULED = 10


NOTIFICATION_JOB_QUEUE_TOPIC = 'NOTIFICATION_JOB_QUEUE'


async def publish_notification_job(
    redis_conn: RedisConnection,
    job: NotificationJob,
    priority: NotificationPriority = NotificationPriority.IMMEDIATE,
):
    return await zadd(
        redis_conn=redis_conn,
        topic=NOTIFICATION_JOB_QUEUE_TOPIC,
        job=dataclasses.asdict(job),
        z_index=int(priority)
    )


async def blocking_get_notification_job(
    redis_conn: RedisConnection,
    timeout: int = 0
) -> Optional[NotificationJob]:
    job_json = await bzpopmin(
        redis_conn=redis_conn,
        topic=NOTIFICATION_JOB_QUEUE_TOPIC,
        timeout=timeout
    )
    if not job_json:
        return None

    job = json.loads(job_json)
    return deserialize.deserialize(NotificationJob, job)
