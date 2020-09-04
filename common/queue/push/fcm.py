import dataclasses
import json
from typing import Optional

import deserialize
from aioredis import RedisConnection

from common.queue import rpush, blpop
from common.structure.job.fcm import FCMJob

FCM_PUSH_QUEUE_TOPIC = 'FCM_PUSH_QUEUE'


async def publish_fcm_job(
    redis_conn: RedisConnection,
    job: FCMJob,
):
    return await rpush(
        redis_conn=redis_conn,
        topic=FCM_PUSH_QUEUE_TOPIC,
        job=dataclasses.asdict(job)
    )


async def blocking_get_fcm_job(
    redis_conn: RedisConnection,
    timeout: int = 0
) -> Optional[FCMJob]:
    job_json = await blpop(
        redis_conn=redis_conn,
        topic=FCM_PUSH_QUEUE_TOPIC,
        timeout=timeout
    )
    if not job_json:
        return None

    job = json.loads(job_json)
    return deserialize.deserialize(FCMJob, job)
