import dataclasses
import json
from typing import Optional

import deserialize
from aioredis import RedisConnection

from common.queue import rpush, blpop
from common.structure.job.messaging import MessagingJob

MESSAGING_QUEUE = 'MESSAGING_QUEUE'


async def publish_messaging_job(
    redis_conn: RedisConnection,
    job: MessagingJob,
):
    return await rpush(
        redis_conn=redis_conn,
        topic=MESSAGING_QUEUE,
        job=dataclasses.asdict(job)
    )


async def blocking_get_messaging_job(
    redis_conn: RedisConnection,
    timeout: int = 0
) -> Optional[MessagingJob]:
    job_json = await blpop(
        redis_conn=redis_conn,
        topic=MESSAGING_QUEUE,
        timeout=timeout
    )
    if not job_json:
        return None

    job = json.loads(job_json)
    return deserialize.deserialize(MessagingJob, job)
