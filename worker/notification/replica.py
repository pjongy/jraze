import asyncio
import json
import multiprocessing

import aioredis
import deserialize

from common.logger.logger import get_logger
from common.queue.notification import blocking_get_notification_job, publish_notification_job, \
    NotificationPriority
from common.queue.push.apns import publish_apns_job
from common.queue.push.fcm import publish_fcm_job
from common.structure.condition import ConditionClause
from common.structure.enum import DevicePlatform, SendPlatform
from common.structure.job.notification import NotificationJob, Notification
from common.util import object_to_dict, string_to_utc_datetime, utc_now
from worker.notification.config import config
from worker.notification.external.jraze.jraze import JrazeApi

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
        self.jraze_api = JrazeApi()

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
        search_device_result = await self.jraze_api.search_devices(
            conditions=object_to_dict(conditions),
            start=start,
            size=size,
        )
        device_platforms = {DevicePlatform.IOS, DevicePlatform.Android}
        send_platforms = {SendPlatform.APNS, SendPlatform.FCM}

        tokens = {}
        for send_platform in send_platforms:
            if send_platform not in tokens:
                tokens[send_platform] = {}
            for device_platform in device_platforms:
                if device_platform not in tokens[send_platform]:
                    tokens[send_platform][device_platform] = []

        device_ids = []
        for device in search_device_result.result.devices:
            tokens[device.send_platform][device.device_platform].append(device.push_token)
            device_ids.append(device.id)

        tasks = [
            self.jraze_api.log_notification(
                device_ids=device_ids,
                notification_id=notification.id,
            ),
        ]

        for send_platform in send_platforms:
            for device_platform in device_platforms:
                if send_platform == SendPlatform.FCM:
                    tasks.append(
                        self._publish_job_to_fcm(fcm_job={
                            'push_tokens': tokens[send_platform][device_platform],
                            'device_platform': device_platform.value,
                            'id': str(notification.uuid),
                            'body': notification.body,
                            'title': notification.title,
                            'deep_link': notification.deep_link,
                            'image_url': notification.image_url,
                            'icon_url': notification.icon_url
                        })
                    )
                if send_platform == SendPlatform.APNS:
                    tasks.append(
                        self._publish_job_to_apns(apns_job={
                            'device_tokens': tokens[send_platform][device_platform],
                            'device_platform': device_platform.value,
                            'id': str(notification.uuid),
                            'body': notification.body,
                            'title': notification.title,
                            'deep_link': notification.deep_link,
                            'image_url': notification.image_url,
                            'icon_url': notification.icon_url
                        })
                    )
        await asyncio.gather(*tasks)

    async def _publish_job_to_fcm(self, fcm_job: dict):
        with await self.redis_pool as redis_conn:
            pushed_job_count = await publish_fcm_job(
                redis_conn=redis_conn,
                job=fcm_job,
            )
            return pushed_job_count

    async def _publish_job_to_apns(self, apns_job: dict):
        with await self.redis_pool as redis_conn:
            pushed_job_count = await publish_apns_job(
                redis_conn=redis_conn,
                job=apns_job,
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
                # TODO(pjongy): Fix divide by zero
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
