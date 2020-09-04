import dataclasses
import json
from typing import Optional

import deserialize
from aioredis import RedisConnection

from common.queue import rpush, blpop
from common.structure.job.apns import APNsJob

APNS_PUSH_QUEUE_TOPIC = 'APNS_PUSH_QUEUE'


async def publish_apns_job(
    redis_conn: RedisConnection,
    job: APNsJob,
):
    return await rpush(
        redis_conn=redis_conn,
        topic=APNS_PUSH_QUEUE_TOPIC,
        job=dataclasses.asdict(job)
    )


async def blocking_get_apns_job(
    redis_conn: RedisConnection,
    timeout: int = 0
) -> Optional[APNsJob]:
    job_json = await blpop(
        redis_conn=redis_conn,
        topic=APNS_PUSH_QUEUE_TOPIC,
        timeout=timeout
    )
    if not job_json:
        return None

    job = json.loads(job_json)
    return deserialize.deserialize(APNsJob, job)
