import asyncio
import json
import multiprocessing

import aioredis
import deserialize

from common.logger.logger import get_logger
from common.queue.push.fcm import blocking_get_fcm_job
from common.queue.result.push import publish_push_result_job
from common.structure.job.fcm import FCMJob
from worker.push.fcm.config import config
from worker.push.fcm.external.fcm.abstract import AbstractFCM
from worker.push.fcm.external.fcm.legacy import FCMClientLegacy
from worker.push.fcm.external.fcm.v1 import FCMClientV1

logger = get_logger(__name__)


class Replica:
    REDIS_TIMEOUT = 0  # Infinite

    def __init__(self, pid):
        self.fcm: AbstractFCM = self.create_fcm_client()
        self.redis_host = config.push_worker.redis.host
        self.redis_port = config.push_worker.redis.port
        self.redis_password = config.push_worker.redis.password
        self.redis_pool = None

        logger.debug(f'Worker {pid} up')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.job())

    def create_fcm_client(self) -> AbstractFCM:
        fcm_config = config.push_worker.fcm
        if config.push_worker.fcm.client == 'legacy':
            return FCMClientLegacy(fcm_config.legacy.server_key)
        elif config.push_worker.fcm.client == 'v1':
            return FCMClientV1(fcm_config.v1.project_id, fcm_config.v1.key_file_name)
        else:
            raise ValueError(f'fcm client not allow: {config.push_worker.fcm.client}')

    async def process_job(self, job_json):  # real worker if job published
        try:
            logger.debug(job_json)
            job: FCMJob = deserialize.deserialize(
                FCMJob, json.loads(job_json)
            )
            if not job.push_tokens:
                return

            sent, failed = await self.fcm.send_data(
                targets=job.push_tokens,
                data={
                    'notification': {
                        'title': job.title,
                        'body': job.body,
                        'image': job.image_url,
                    }
                }
            )
            logger.info(f'sent: {sent}, failed: {failed}')

            if job.id:
                with await self.redis_pool as redis_conn:
                    await publish_push_result_job(
                        redis_conn=redis_conn,
                        job={
                            'id': job.id,
                            'sent': sent,
                            'device_platform': job.device_platform,
                            'failed': failed,
                        }
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
                job_json = await blocking_get_fcm_job(
                    redis_conn=redis_conn,
                    timeout=self.REDIS_TIMEOUT
                )
                logger.debug(multiprocessing.current_process())

                if not job_json:
                    continue

                logger.info('new task')
                asyncio.create_task(self.process_job(job_json))
