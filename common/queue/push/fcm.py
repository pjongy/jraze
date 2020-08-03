from aioredis import RedisConnection

from common.queue import rpush, blpop

FCM_PUSH_QUEUE_TOPIC = 'FCM_PUSH_QUEUE'


async def publish_fcm_job(
    redis_conn: RedisConnection,
    job: dict,
):
    return await rpush(
        redis_conn=redis_conn,
        topic=FCM_PUSH_QUEUE_TOPIC,
        job=job
    )


async def blocking_get_fcm_job(
    redis_conn: RedisConnection,
    timeout: int = 0
) -> str:
    return await blpop(
        redis_conn=redis_conn,
        topic=FCM_PUSH_QUEUE_TOPIC,
        timeout=timeout
    )
