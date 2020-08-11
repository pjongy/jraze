import asyncio
import json
import multiprocessing

import aioredis
import deserialize

from common.logger.logger import get_logger
from common.queue.push.apns import blocking_get_apns_job
from common.queue.result.push import publish_push_result_job
from common.structure.job.apns import APNsJob
from worker.push.apns.auth.jwt import AppleJWT
from worker.push.apns.config import config
from worker.push.apns.external.apns.v3 import APNsV3

logger = get_logger(__name__)


class Replica:
    REDIS_TIMEOUT = 0  # Infinite

    def __init__(self, pid):
        apns_config = config.push_worker.apns
        self.apns = APNsV3(
            apple_jwt=AppleJWT(
                key_file_name=apns_config.key_file_name,
                key_id=apns_config.key_id,
                team_id=apns_config.team_id,
            )
        )
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
            job: APNsJob = deserialize.deserialize(
                APNsJob, json.loads(job_json)
            )
            if not job.device_tokens:
                return

            sent, failed = await self.apns.send_data(
                targets=job.device_tokens,
                data={
                    'alert': {
                        'title': job.title,
                        'body': job.body,
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
                job_json = await blocking_get_apns_job(
                    redis_conn=redis_conn,
                    timeout=self.REDIS_TIMEOUT
                )
                logger.debug(multiprocessing.current_process())

                if not job_json:
                    continue

                logger.info('new task')
                asyncio.create_task(self.process_job(job_json))
