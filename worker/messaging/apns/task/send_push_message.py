import dataclasses

import deserialize
from jasyncq.dispatcher.model.task import TaskIn
from jasyncq.dispatcher.tasks import TasksDispatcher

from common.logger.logger import get_logger
from common.structure.job.messaging import SendPushMessageArgs
from common.structure.job.notification import NotificationJob, NotificationTask
from worker.messaging.apns.external.apns.abstract import AbstractAPNs
from worker.messaging.apns.task import AbstractTask

logger = get_logger(__name__)


class SendPushMessageTask(AbstractTask):
    def __init__(
        self,
        apns: AbstractAPNs,
        notification_task_queue: TasksDispatcher,
    ):
        self.apns: AbstractAPNs = apns
        self.notification_task_queue = notification_task_queue

    async def run(self, kwargs: dict):
        logger.debug(kwargs)
        task_args: SendPushMessageArgs = deserialize.deserialize(SendPushMessageArgs, kwargs)
        if not task_args.push_tokens:
            return

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
