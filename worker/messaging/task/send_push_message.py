import dataclasses

import deserialize
from jasyncq.dispatcher.model.task import TaskIn
from jasyncq.dispatcher.tasks import TasksDispatcher

from common.logger.logger import get_logger
from common.structure.job.messaging import SendPushMessageArgs, SendPlatform
from common.structure.job.notification import NotificationJob, NotificationTask
from worker.messaging.external.apns.abstract import AbstractAPNs
from worker.messaging.external.fcm.abstract import AbstractFCM
from worker.messaging.task import AbstractTask

logger = get_logger(__name__)


class SendPushMessageTask(AbstractTask):
    def __init__(
        self,
        fcm: AbstractFCM,
        apns: AbstractAPNs,
        notification_task_queue: TasksDispatcher,
    ):
        self.fcm: AbstractFCM = fcm
        self.apns: AbstractAPNs = apns
        self.notification_task_queue = notification_task_queue

    async def run(self, kwargs: dict):
        logger.debug(kwargs)
        task_args: SendPushMessageArgs = deserialize.deserialize(SendPushMessageArgs, kwargs)
        if not task_args.push_tokens:
            return

        if task_args.send_platform == SendPlatform.FCM:
            sent, failed = await self.fcm.send_data(
                targets=task_args.push_tokens,
                data={
                    'notification': {
                        'title': task_args.title,
                        'body': task_args.body,
                        'image': task_args.image_url,
                    }
                }
            )
        elif task_args.send_platform == SendPlatform.APNS:
            sent, failed = await self.apns.send_data(
                targets=task_args.push_tokens,
                data={
                    'aps': {
                        'alert': {
                            'title': task_args.title,
                            'body': task_args.body,
                        }
                    }
                }
            )
        else:
            raise NotImplementedError(
                f'Can not handle SendPlatform type {task_args.send_platform.name}')

        logger.info(f'sent: {sent}, failed: {failed}')
        await self.notification_task_queue.apply_tasks(
            tasks=[
                TaskIn(
                    task=dataclasses.asdict(deserialize.deserialize(NotificationJob, {
                        'task': NotificationTask.UPDATE_RESULT,
                        'kwargs': {
                            'device_platform': task_args.device_platform,
                            'notification_uuid': task_args.notification_id,
                            'sent': sent,
                            'failed': failed,
                        }
                    })),
                    queue_name='NOTIFICATION_JOB_QUEUE',
                )
            ],
        )
