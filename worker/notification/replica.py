import asyncio
import json
import multiprocessing

import aioredis
import deserialize

from common.logger.logger import get_logger
from common.model.device import SendPlatform
from common.model.notification import Notification
from common.storage.init import init_db
from common.structure.condition import ConditionClause
from common.structure.job.fcm import FCMJob
from common.structure.job.notification import NotificationJob
from common.util import object_to_dict
from worker.notification.config import config
from worker.notification.repository.device import find_devices_by_conditions, \
    get_device_total_by_conditions
from worker.notification.repository.notification import find_notification_by_id

logger = get_logger(__name__)


class Replica:
    NOTIFICATION_JOB_QUEUE_TOPIC = 'NOTIFICATION_JOB_QUEUE'
    FCM_PUSH_QUEUE_TOPIC = 'FCM_PUSH_QUEUE'
    REDIS_TIMEOUT = 0  # Infinite
    DEVICES_PER_ONCE_SIZE = 100
    TOTAL_WORKERS = int(config.notification_worker.pool_size)

    def __init__(self):
        self.redis_host = config.notification_worker.redis.host
        self.redis_port = config.notification_worker.redis.port
        self.redis_password = config.notification_worker.redis.password
        self.redis_pool = None
        self.pid = None

    def run(self, pid):  # multiprocess child
        self.pid = pid
        logger.debug(f'Worker {pid} up')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.job())

    async def _find_devices_and_publish(
        self,
        job_id: str,
        title: str,
        body: str,
        conditions: ConditionClause,
        start: int,
        size: int
    ):
        devices = await find_devices_by_conditions(
            conditions=conditions,
            start=start,
            size=size,
        )
        fcm_tokens = []

        for device in devices:
            if device.send_platform == SendPlatform.FCM:
                fcm_tokens.append(device.push_token)

        job = FCMJob()
        job.push_tokens = fcm_tokens
        job.body = body
        job.id = job_id
        job.title = title
        await self._publish_job_to_fcm(fcm_job=job)

    async def _send_with_notification(self, notification: Notification):
        conditions = deserialize.deserialize(ConditionClause, notification.conditions)
        device_total = await get_device_total_by_conditions(
            conditions=conditions
        )
        iter_count = int(device_total / self.DEVICES_PER_ONCE_SIZE / self.TOTAL_WORKERS) + 1

        tasks = [
            self._find_devices_and_publish(
                job_id=str(notification.id),
                title=notification.title,
                body=notification.body,
                conditions=conditions,
                start=iteration * self.pid * self.DEVICES_PER_ONCE_SIZE,
                size=self.DEVICES_PER_ONCE_SIZE,
            )
            for iteration in range(iter_count)
        ]
        await asyncio.gather(*tasks)

    async def _publish_job_to_fcm(self, fcm_job: FCMJob):
        with await self.redis_pool as redis_conn:
            pushed_job_count = await redis_conn.execute(
                'rpush',
                self.FCM_PUSH_QUEUE_TOPIC,
                json.dumps(object_to_dict(fcm_job)),
            )
            return pushed_job_count

    async def process_job(self, job_json):  # real worker if job published
        try:
            logger.debug(job_json)
            job: NotificationJob = deserialize.deserialize(
                NotificationJob, json.loads(job_json)
            )

            if job.notification_id is not None:
                notification = await find_notification_by_id(
                    _id=job.notification_id,
                )
                if notification is None:
                    logger.warning('invalid notification id')
                await self._send_with_notification(notification)
        except Exception:
            logger.exception(f'Fatal Error! {job_json}')

    async def job(self):  # real working job
        mysql_config = config.notification_worker.mysql
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
            db=int(config.notification_worker.redis.notification_queue.database),
            minsize=5,
            maxsize=10,
        )
        while True:
            with await self.redis_pool as redis_conn:
                _, job_json = await redis_conn.execute(
                    'blpop',
                    self.NOTIFICATION_JOB_QUEUE_TOPIC,
                    self.REDIS_TIMEOUT,
                )
                logger.debug(multiprocessing.current_process())

                if not job_json:
                    continue

                logger.info('new task')
                asyncio.create_task(self.process_job(job_json))
