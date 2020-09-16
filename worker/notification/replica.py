import asyncio
import dataclasses
import multiprocessing
from typing import Dict

import aioredis

from common.logger.logger import get_logger
from common.queue.notification import blocking_get_notification_job
from common.structure.job.notification import NotificationJob, NotificationTask
from worker.notification.config import config
from worker.notification.external.jraze.jraze import JrazeApi
from worker.notification.task import AbstractTask
from worker.notification.task.launch_notification import LaunchNotificationTask
from worker.notification.task.update_push_result import UpdatePushResultTask

logger = get_logger(__name__)


class Replica:
    REDIS_TIMEOUT = 0  # Infinite
    DEVICES_PER_ONCE_SIZE = 300
    TOTAL_WORKERS = int(config.notification_worker.pool_size)

    def __init__(self, pid):
        loop = asyncio.get_event_loop()

        redis_host = config.notification_worker.redis.host
        redis_port = config.notification_worker.redis.port
        redis_password = config.notification_worker.redis.password
        self.redis_pool = loop.run_until_complete(
            aioredis.create_pool(
                f'redis://{redis_host}:{redis_port}',
                password=redis_password,
                db=int(config.notification_worker.redis.notification_queue.database),
                minsize=5,
                maxsize=10,
            )
        )

        self.jraze_api = JrazeApi()
        self.tasks: Dict[NotificationTask, AbstractTask] = {
            NotificationTask.LAUNCH_NOTIFICATION: LaunchNotificationTask(
                jraze_api=self.jraze_api,
                redis_pool=self.redis_pool,
            ),
            NotificationTask.UPDATE_RESULT: UpdatePushResultTask(
                jraze_api=self.jraze_api,
            ),
        }
        loop.run_until_complete(self.job())

        logger.debug(f'Worker {pid} up')

    async def process_job(self, job: NotificationJob):  # real worker if job published
        try:
            logger.debug(job)
            try:
                task = self.tasks[job.task]
            except KeyError as e:
                logger.warning(f'unknown task({job.task.name}): {e}')
                return

            await task.run(kwargs=job.kwargs)
        except Exception:
            logger.exception(f'Fatal Error! {dataclasses.asdict(job)}')

    async def job(self):  # real working job
        while True:
            with await self.redis_pool as redis_conn:
                job = await blocking_get_notification_job(
                    redis_conn=redis_conn,
                    timeout=self.REDIS_TIMEOUT
                )
                logger.debug(multiprocessing.current_process())

                if not job:
                    continue

                logger.info('new task')
                asyncio.create_task(self.process_job(job=job))
