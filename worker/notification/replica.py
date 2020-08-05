import asyncio
import json
import multiprocessing
import time

import aioredis
import deserialize

from common.logger.logger import get_logger
from common.model.device import SendPlatform
from common.model.device_notification_event import Event
from common.queue.notification import blocking_get_notification_job, publish_notification_job, \
    NotificationPriority
from common.queue.push.fcm import publish_fcm_job
from common.storage.init import init_db
from common.structure.condition import ConditionClause
from common.structure.job.fcm import FCMJob
from common.structure.job.notification import NotificationJob, Notification
from common.util import object_to_dict, string_to_utc_datetime, utc_now
from worker.notification.config import config
from worker.notification.repository.device import find_devices_by_conditions
from worker.notification.repository.device_notification_event import add_device_notification_events

logger = get_logger(__name__)


class Replica:
    REDIS_TIMEOUT = 0  # Infinite
    DEVICES_PER_ONCE_SIZE = 300
    TOTAL_WORKERS = int(config.notification_worker.pool_size)

    def __init__(self, pid):
        self.redis_host = config.notification_worker.redis.host
        self.redis_port = config.notification_worker.redis.port
        self.redis_password = config.notification_worker.redis.password
        self.redis_pool = None

        logger.debug(f'Worker {pid} up')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.job())

    async def _send_notification_by_conditions(
        self,
        notification: Notification,
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

        job: FCMJob = deserialize.deserialize(
            FCMJob, {
                'push_tokens': fcm_tokens,
                'id': str(notification.uuid),
                'body': notification.body,
                'title': notification.title,
                'deep_link': notification.deep_link,
                'image_url': notification.image_url,
                'icon_url': notification.icon_url
            }
        )
        tasks = [
            add_device_notification_events(
                devices=devices,
                notification_id=notification.id,
                event=Event.SENT,
            ),
            self._publish_job_to_fcm(fcm_job=job)
        ]
        await asyncio.gather(*tasks)

    async def _publish_job_to_fcm(self, fcm_job: FCMJob):
        with await self.redis_pool as redis_conn:
            pushed_job_count = await publish_fcm_job(
                redis_conn=redis_conn,
                job=object_to_dict(fcm_job)
            )
            return pushed_job_count

    async def process_job(self, job: NotificationJob):  # real worker if job published
        try:
            if job.notification is not None:
                notification: Notification = job.notification
                worker_own_jobs = job.notification.devices.size
                start_position = job.notification.devices.start

                fetching_size = min(worker_own_jobs, self.DEVICES_PER_ONCE_SIZE)
                iter_count = int(worker_own_jobs / fetching_size)
                # NOTE:
                # If worker_own_jobs is smaller than DEVICE_PER_ONCE_SIZE,
                # target devices overlap in each notification worker replica

                fetching_ranges = [
                    (start_position + iteration * fetching_size, fetching_size)
                    for iteration in range(iter_count)
                ]
                if worker_own_jobs % fetching_size > 0:
                    fetching_ranges.append((
                        start_position + iter_count * fetching_size,
                        worker_own_jobs % fetching_size
                    ))
                # NOTE: Split cases for covering 'worker_own_jobs % fetching_size != 0'
                tasks = [
                    self._send_notification_by_conditions(
                        notification=notification,
                        conditions=job.notification.conditions,
                        start=start,
                        size=size,
                    )
                    for start, size in fetching_ranges
                ]
                await asyncio.gather(*tasks)
        except BaseException as e:
            logger.exception(f'fatal error! {e}')

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
                job_json = await blocking_get_notification_job(
                    redis_conn=redis_conn,
                    timeout=self.REDIS_TIMEOUT
                )
                logger.debug(multiprocessing.current_process())

                if not job_json:
                    continue

                logger.debug(job_json)
                job: NotificationJob = deserialize.deserialize(
                    NotificationJob, json.loads(job_json)
                )

                scheduled_at = string_to_utc_datetime(job.scheduled_at)
                current_datetime = utc_now()
                if scheduled_at > current_datetime:
                    await publish_notification_job(
                        redis_conn=redis_conn,
                        job=object_to_dict(job),
                        priority=NotificationPriority.SCHEDULED,
                    )
                    logger.debug('scheduled notification (passed)')
                    await asyncio.sleep(1)
                    continue

                logger.info('new task')
                asyncio.create_task(self.process_job(job=job))
