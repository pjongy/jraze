import asyncio
import json
import multiprocessing

import aioredis
import deserialize

from common.logger.logger import get_logger
from common.queue.result.push import blocking_get_push_result_job
from common.structure.enum import DevicePlatform
from common.structure.job.result import ResultJob
from worker.result.config import config

from worker.result.external.jraze.jraze import JrazeApi

logger = get_logger(__name__)


class Replica:
    REDIS_TIMEOUT = 0  # Infinite

    def __init__(self, pid):
        self.redis_host = config.result_worker.redis.host
        self.redis_port = config.result_worker.redis.port
        self.redis_password = config.result_worker.redis.password
        self.redis_pool = None
        self.jraze_api = JrazeApi()

        logger.debug(f'Worker {pid} up')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.job())

    async def process_job(self, job_json):  # real worker if job published
        try:
            logger.debug(job_json)
            job: ResultJob = deserialize.deserialize(
                ResultJob, json.loads(job_json)
            )
            if job.device_platform == DevicePlatform.IOS:
                await self.jraze_api.increase_notification_sent(
                    notification_uuid=job.id,
                    ios=job.sent,
                )
            elif job.device_platform == DevicePlatform.Android:
                await self.jraze_api.increase_notification_sent(
                    notification_uuid=job.id,
                    android=job.sent,
                )
            else:
                logger.warning(f'unknown device_platform: {job.device_platform}')

            logger.info(f'increased sent({job.device_platform.name}): {job.sent} for {job.id}')
        except Exception:
            logger.exception(f'Fatal Error! {job_json}')

    async def job(self):  # real working job
        self.redis_pool = await aioredis.create_pool(
            f'redis://{self.redis_host}:{self.redis_port}',
            password=self.redis_password,
            db=int(config.result_worker.redis.notification_queue.database),
            minsize=5,
            maxsize=10,
        )
        while True:
            with await self.redis_pool as redis_conn:
                job_json = await blocking_get_push_result_job(
                    redis_conn=redis_conn,
                    timeout=self.REDIS_TIMEOUT
                )
                logger.debug(multiprocessing.current_process())

                if not job_json:
                    continue

                logger.info('new task')
                asyncio.create_task(self.process_job(job_json))
