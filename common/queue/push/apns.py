from aioredis import RedisConnection

from common.queue import rpush, blpop

APNS_PUSH_QUEUE_TOPIC = 'APNS_PUSH_QUEUE'


async def publish_apns_job(
    redis_conn: RedisConnection,
    job: dict,
):
    return await rpush(
        redis_conn=redis_conn,
        topic=APNS_PUSH_QUEUE_TOPIC,
        job=job
    )


async def blocking_get_apns_job(
    redis_conn: RedisConnection,
    timeout: int = 0
) -> str:
    return await blpop(
        redis_conn=redis_conn,
        topic=APNS_PUSH_QUEUE_TOPIC,
        timeout=timeout
    )
