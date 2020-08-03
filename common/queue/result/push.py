from aioredis import RedisConnection

from common.queue import rpush, blpop

PUSH_RESULT_QUEUE_TOPIC = 'PUSH_RESULT_QUEUE'


async def publish_push_result_job(
    redis_conn: RedisConnection,
    job: dict,
):
    return await rpush(
        redis_conn=redis_conn,
        topic=PUSH_RESULT_QUEUE_TOPIC,
        job=job
    )


async def blocking_get_push_result_job(
    redis_conn: RedisConnection,
    timeout: int = 0
) -> str:
    return await blpop(
        redis_conn=redis_conn,
        topic=PUSH_RESULT_QUEUE_TOPIC,
        timeout=timeout
    )
