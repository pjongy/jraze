import json

from aioredis import RedisConnection

from common.json_encoder import ManualJSONEncoder


async def rpush(
    redis_conn: RedisConnection,
    topic: str,
    job: dict,
):
    return await redis_conn.execute(
        'rpush',
        topic,
        json.dumps(job, cls=ManualJSONEncoder),
    )


async def blpop(
    redis_conn: RedisConnection,
    topic: str,
    timeout: int = 0
) -> str:
    # NOTE: timeout 0 means infinite
    _, data = await redis_conn.execute(
        'blpop',
        topic,
        timeout,
    )
    return data


async def zadd(
    redis_conn: RedisConnection,
    topic: str,
    job: dict,
    z_index: int = 0,
):
    # NOTE: priority closed to 0 means more urgent because of using BZPOPMIN
    return await redis_conn.execute(
        'zadd',
        topic,
        z_index,
        json.dumps(job, cls=ManualJSONEncoder),
    )


async def bzpopmin(
    redis_conn: RedisConnection,
    topic: str,
    timeout: int = 0
) -> str:
    # NOTE: timeout 0 means infinite
    _, data, z_index = await redis_conn.execute(
        'bzpopmin',
        topic,
        timeout,
    )
    return data
