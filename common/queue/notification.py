import enum

from aioredis import RedisConnection

from common.queue import zadd, bzpopmin


class NotificationPriority(enum.IntEnum):
    IMMEDIATE = 0
    SCHEDULED = 10


NOTIFICATION_JOB_QUEUE_TOPIC = 'NOTIFICATION_JOB_QUEUE'


async def publish_notification_job(
    redis_conn: RedisConnection,
    job: dict,
    priority: NotificationPriority = NotificationPriority.IMMEDIATE,
):
    return await zadd(
        redis_conn=redis_conn,
        topic=NOTIFICATION_JOB_QUEUE_TOPIC,
        job=job,
        z_index=int(priority)
    )


async def blocking_get_notification_job(
    redis_conn: RedisConnection,
    timeout: int = 0
) -> str:
    return await bzpopmin(
        redis_conn=redis_conn,
        topic=NOTIFICATION_JOB_QUEUE_TOPIC,
        timeout=timeout
    )
