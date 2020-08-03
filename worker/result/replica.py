import asyncio
import json
import multiprocessing

import aioredis
import deserialize

from common.logger.logger import get_logger
from common.model.notification import NotificationStatus
from common.queue.result.push import blocking_get_push_result_job
from common.storage.init import init_db
from common.structure.job.result import ResultJob
from worker.result.config import config
from worker.result.repository.notification import increase_sent_count, change_notification_status

logger = get_logger(__name__)


class Replica:
    REDIS_TIMEOUT = 0  # Infinite

    def __init__(self, pid):
        self.redis_host = config.result_worker.redis.host
        self.redis_port = config.result_worker.redis.port
        self.redis_password = config.result_worker.redis.password
        self.redis_pool = None

        logger.debug(f'Worker {pid} up')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.job())

    async def process_job(self, job_json):  # real worker if job published
        try:
            logger.debug(job_json)
            job: ResultJob = deserialize.deserialize(
                ResultJob, json.loads(job_json)
            )
            affected_row = await increase_sent_count(
                uuid=job.id,
                sent=job.sent,
            )
            logger.info(f'increased sent: {job.sent} for {job.id} / affected_row: {affected_row}')
            await change_notification_status(
                uuid=job.id,
                status=NotificationStatus.SENT,
            )
        except Exception:
            logger.exception(f'Fatal Error! {job_json}')

    async def job(self):  # real working job
        mysql_config = config.result_worker.mysql
        await init_db(
            host=mysql_config.host,
            port=mysql_config.port,
            user=mysql_config.user,
            password=mysql_config.password,
            db=mysql_config.database,
        )
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
