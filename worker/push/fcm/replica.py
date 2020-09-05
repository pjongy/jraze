import asyncio
import dataclasses
import multiprocessing
from typing import Dict

import aioredis

from common.logger.logger import get_logger
from common.queue.push.fcm import blocking_get_fcm_job
from common.queue.result.push import publish_push_result_job
from common.structure.job.fcm import FCMJob, FCMTask
from common.structure.job.result import ResultJob
from worker.push.fcm.config import config
from worker.push.fcm.external.fcm.abstract import AbstractFCM
from worker.push.fcm.external.fcm.legacy import FCMClientLegacy
from worker.push.fcm.external.fcm.v1 import FCMClientV1
from worker.push.fcm.task import AbstractTask
from worker.push.fcm.task.send_push_message import SendPushMessageTask

logger = get_logger(__name__)


class Replica:
    REDIS_TIMEOUT = 0  # Infinite

    def __init__(self, pid):
        self.redis_host = config.push_worker.redis.host
        self.redis_port = config.push_worker.redis.port
        self.redis_password = config.push_worker.redis.password
        self.redis_pool = None

        fcm: AbstractFCM = self.create_fcm_client()
        self.tasks: Dict[FCMTask, AbstractTask] = {
            FCMTask.SEND_PUSH_MESSAGE: SendPushMessageTask(fcm=fcm)
        }

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

    async def process_job(self, job: FCMJob):  # real worker if job published
        try:
            logger.debug(job)
            try:
                task = self.tasks[job.task]
            except KeyError as e:
                logger.warning(f'unknown task({job.task.name}): {e}')
                return

            result_job = await task.run(kwargs=job.kwargs)
            if not result_job:
                return

            await self._publish_job_to_result_queue(
                result_job=result_job
            )
        except Exception:
            logger.exception(f'Fatal Error! {dataclasses.asdict(job)}')

    async def _publish_job_to_result_queue(self, result_job: ResultJob):
        with await self.redis_pool as redis_conn:
            pushed_job_count = await publish_push_result_job(
                redis_conn=redis_conn,
                job=result_job
            )
            return pushed_job_count

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
                job = await blocking_get_fcm_job(
                    redis_conn=redis_conn,
                    timeout=self.REDIS_TIMEOUT
                )
                logger.debug(multiprocessing.current_process())

                if not job:
                    continue

                logger.info('new task')
                asyncio.create_task(self.process_job(job))
