import asyncio
import json
import multiprocessing

import aioredis
import deserialize

from common.logger.logger import get_logger
from common.structure.job.fcm import FCMJob
from worker.push.fcm.config import config
from worker.push.fcm.external.fcm import FCM

logger = get_logger(__name__)


class Replica:
    FCM_PUSH_QUEUE_TOPIC = 'FCM_PUSH_QUEUE'
    PUSH_RESULT_QUEUE_TOPIC = 'PUSH_RESULT_QUEUE'
    REDIS_TIMEOUT = 0  # Infinite

    def __init__(self, pid):
        self.fcm = FCM(config.push_worker.firebase.server_key)
        self.redis_host = config.push_worker.redis.host
        self.redis_port = config.push_worker.redis.port
        self.redis_password = config.push_worker.redis.password
        self.redis_pool = None

        logger.debug(f'Worker {pid} up')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.job())

    async def process_job(self, job_json):  # real worker if job published
        try:
            logger.debug(job_json)
            job: FCMJob = deserialize.deserialize(
                FCMJob, json.loads(job_json)
            )

            sent, failed = await self.fcm.send_notification(
                targets=job.push_tokens,
                title=job.title,
                body=job.body,
                image=job.image_url,
            )
            logger.info(f'sent: {sent}, failed: {failed}')

            if job.id:
                with await self.redis_pool as redis_conn:
                    _ = await redis_conn.execute(
                        'rpush',
                        self.PUSH_RESULT_QUEUE_TOPIC,
                        json.dumps({
                            'id': job.id,
                            'sent': sent,
                            'failed': failed,
                        }),
                    )
        except Exception:
            logger.exception(f'Fatal Error! {job_json}')

    async def job(self):  # real working job
        self.redis_pool = await aioredis.create_pool(
            f'redis://{self.redis_host}:{self.redis_port}',
            password=self.redis_password,
            db=int(config.push_worker.redis.notification_queue.database),
            minsize=5,
            maxsize=10,
        )
        while True:
            with await self.redis_pool as redis_conn:
                _, job_json = await redis_conn.execute(
                    'blpop',
                    self.FCM_PUSH_QUEUE_TOPIC,
                    self.REDIS_TIMEOUT,
                )
                logger.debug(multiprocessing.current_process())

                if not job_json:
                    continue

                logger.info('new task')
                asyncio.create_task(self.process_job(job_json))
