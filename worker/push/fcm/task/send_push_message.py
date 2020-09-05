from typing import Optional

import deserialize

from common.logger.logger import get_logger
from common.structure.job.fcm import FCMSendPushMessageArgs
from common.structure.job.result import ResultJob
from worker.push.fcm.external.fcm.abstract import AbstractFCM
from worker.push.fcm.task import AbstractTask

logger = get_logger(__name__)


class SendPushMessageTask(AbstractTask):
    def __init__(self, fcm: AbstractFCM):
        self.fcm: AbstractFCM = fcm

    async def run(self, kwargs: dict) -> Optional[ResultJob]:
        logger.debug(kwargs)
        task_args: FCMSendPushMessageArgs = deserialize.deserialize(FCMSendPushMessageArgs, kwargs)
        try:
            if not task_args.push_tokens:
                return

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
            logger.info(f'sent: {sent}, failed: {failed}')
            return deserialize.deserialize(ResultJob, {
                'id': task_args.notification_id,
                'sent': sent,
                'device_platform': task_args.device_platform,
                'failed': failed,
            })
        except Exception:
            logger.exception(f'Fatal Error! {kwargs}')
