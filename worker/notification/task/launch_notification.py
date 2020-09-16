import asyncio
import dataclasses

import deserialize
from aioredis import ConnectionsPool

from common.logger.logger import get_logger
from common.queue.messaging import publish_messaging_job
from common.structure.enum import DevicePlatform, SendPlatform
from common.structure.job.messaging import MessagingJob, MessagingTask
from common.structure.job.notification import NotificationLaunchMessageArgs, Notification
from worker.notification.external.jraze.jraze import JrazeApi
from worker.notification.task import AbstractTask

logger = get_logger(__name__)


class LaunchNotificationTask(AbstractTask):
    def __init__(self, jraze_api: JrazeApi, redis_pool: ConnectionsPool):
        self.jraze_api: JrazeApi = jraze_api
        self.redis_pool: ConnectionsPool = redis_pool

    async def _publish_messaging_worker_job(self, task_kwargs: dict):
        with await self.redis_pool as redis_conn:
            pushed_job_count = await publish_messaging_job(
                redis_conn=redis_conn,
                job=deserialize.deserialize(MessagingJob, {
                    'task': MessagingTask.SEND_PUSH_MESSAGE,
                    'kwargs': task_kwargs,
                })
            )
            return pushed_job_count

    async def run(self, kwargs: dict):
        logger.debug(kwargs)
        task_args: NotificationLaunchMessageArgs = deserialize.deserialize(
            NotificationLaunchMessageArgs, kwargs)
        notification: Notification = task_args.notification

        search_device_result = await self.jraze_api.search_devices(
            conditions=dataclasses.asdict(task_args.conditions),
            start=task_args.device_range.start,
            size=task_args.device_range.size,
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
                tasks.append(
                    self._publish_messaging_worker_job(task_kwargs={
                        'send_platform': send_platform,
                        'notification_id': str(notification.uuid),
                        'push_tokens': tokens[send_platform][device_platform],
                        'device_platform': device_platform,
                        'body': notification.body,
                        'title': notification.title,
                        'deep_link': notification.deep_link,
                        'image_url': notification.image_url,
                        'icon_url': notification.icon_url
                    })
                )
        await asyncio.gather(*tasks)
