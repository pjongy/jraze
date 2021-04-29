import asyncio
import dataclasses

import deserialize
from jasyncq.dispatcher.model.task import TaskIn
from jasyncq.dispatcher.tasks import TasksDispatcher

from common.logger.logger import get_logger
from common.structure.enum import DevicePlatform, SendPlatform
from common.structure.job.messaging import MessagingTask
from common.structure.job.notification import NotificationLaunchMessageArgs, Notification
from worker.notification.external.jraze.jraze import JrazeApi
from worker.notification.task import AbstractTask

logger = get_logger(__name__)


class LaunchNotificationTask(AbstractTask):
    def __init__(self, jraze_api: JrazeApi, messaging_task_queue: TasksDispatcher):
        self.jraze_api: JrazeApi = jraze_api
        self.messaging_task_queue = messaging_task_queue

    async def run(self, kwargs: dict):
        logger.debug(kwargs)
        task_args: NotificationLaunchMessageArgs = deserialize.deserialize(
            NotificationLaunchMessageArgs, kwargs)
        notification: Notification = task_args.notification

        start = 0
        size = 300
        while True:
            search_device_result = await self.jraze_api.search_devices(
                conditions=dataclasses.asdict(task_args.conditions),
                start=start,
                size=size,
            )
            devices = search_device_result.result.devices
            if not devices:
                break

            start += len(devices)
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
            for device in devices:
                tokens[device.send_platform][device.device_platform].append(device.push_token)
                device_ids.append(device.id)

            tasks = []
            for send_platform in send_platforms:
                for device_platform in device_platforms:
                    tasks.append({
                        'task': MessagingTask.SEND_PUSH_MESSAGE,
                        'kwargs': {
                            'send_platform': send_platform,
                            'notification_id': str(notification.uuid),
                            'push_tokens': tokens[send_platform][device_platform],
                            'device_platform': device_platform,
                            'body': notification.body,
                            'title': notification.title,
                            'deep_link': notification.deep_link,
                            'image_url': notification.image_url,
                            'icon_url': notification.icon_url
                        }
                    })

            await asyncio.gather(
                self.jraze_api.log_notification(
                    device_ids=device_ids,
                    notification_id=notification.id,
                ),
                self.messaging_task_queue.apply_tasks(
                    tasks=[
                        TaskIn(
                            task=task,
                            queue_name='MESSAGING_QUEUE',
                        )
                        for task in tasks
                    ],
                )
            )
