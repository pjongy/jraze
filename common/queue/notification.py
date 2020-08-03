from aioredis import RedisConnection

from common.queue import zadd, bzpopmin

NOTIFICATION_JOB_QUEUE_TOPIC = 'NOTIFICATION_JOB_QUEUE'


async def publish_notification_job(
    redis_conn: RedisConnection,
    job: dict,
    priority: int = 0,
):
    return await zadd(
        redis_conn=redis_conn,
        topic=NOTIFICATION_JOB_QUEUE_TOPIC,
        job=job,
        z_index=priority
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
