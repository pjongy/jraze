import dataclasses
import json
from typing import Optional

import deserialize
from aioredis import RedisConnection

from common.queue import rpush, blpop
from common.structure.job.result import ResultJob

PUSH_RESULT_QUEUE_TOPIC = 'PUSH_RESULT_QUEUE'


async def publish_push_result_job(
    redis_conn: RedisConnection,
    job: ResultJob,
):
    return await rpush(
        redis_conn=redis_conn,
        topic=PUSH_RESULT_QUEUE_TOPIC,
        job=dataclasses.asdict(job)
    )


async def blocking_get_push_result_job(
    redis_conn: RedisConnection,
    timeout: int = 0
) -> Optional[ResultJob]:
    job_json = await blpop(
        redis_conn=redis_conn,
        topic=PUSH_RESULT_QUEUE_TOPIC,
        timeout=timeout
    )
    if not job_json:
        return None

    job = json.loads(job_json)
    return deserialize.deserialize(ResultJob, job)
