import deserialize

from common.logger.logger import get_logger
from common.structure.job.messaging import DevicePlatform
from common.structure.job.notification import NotificationSentResultMessageArgs
from worker.notification.external.jraze.jraze import JrazeApi
from worker.notification.task import AbstractTask

logger = get_logger(__name__)


class UpdatePushResultTask(AbstractTask):
    def __init__(self, jraze_api: JrazeApi):
        self.jraze_api: JrazeApi = jraze_api

    async def run(self, kwargs: dict):
        task_args: NotificationSentResultMessageArgs = deserialize.deserialize(
            NotificationSentResultMessageArgs, kwargs)

        if task_args.device_platform == DevicePlatform.IOS:
            await self.jraze_api.increase_notification_sent(
                notification_uuid=task_args.notification_uuid,
                ios=task_args.sent,
            )
        elif task_args.device_platform == DevicePlatform.Android:
            await self.jraze_api.increase_notification_sent(
                notification_uuid=task_args.notification_uuid,
                android=task_args.sent,
            )
