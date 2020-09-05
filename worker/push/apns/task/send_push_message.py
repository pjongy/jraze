import asyncio
from typing import Tuple, List, Optional
from uuid import uuid4

import deserialize
from aioapns import APNs, NotificationRequest, PushType

from common.logger.logger import get_logger
from common.structure.job.apns import APNsSendPushMessageArgs
from common.structure.job.result import ResultJob
from worker.push.apns.task import AbstractTask

logger = get_logger(__name__)


class SendPushMessageTask(AbstractTask):
    def __init__(self, apns: APNs):
        self.apns: APNs = apns

    async def run(self, kwargs: dict) -> Optional[ResultJob]:
        logger.debug(kwargs)
        task_args: APNsSendPushMessageArgs = deserialize.deserialize(
            APNsSendPushMessageArgs, kwargs)
        try:
            if not task_args.device_tokens:
                return

            sent, failed = await self._send_notification(
                targets=task_args.device_tokens,
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
            return deserialize.deserialize(ResultJob, {
                'id': task_args.notification_id,
                'sent': sent,
                'device_platform': task_args.device_platform,
                'failed': failed,
            })
        except Exception:
            logger.exception(f'Fatal Error! {kwargs}')

    async def _send_notification(
        self, targets: List[str], data: dict
    ) -> Tuple[int, int]:
        collapse_key = str(uuid4())
        results = await asyncio.gather(*[
            self.apns.send_notification(
                NotificationRequest(
                    device_token=target,
                    message=data,
                    collapse_key=collapse_key,
                    push_type=PushType.ALERT,
                )
            )
            for target in targets
        ])

        success = 0
        failed = len(targets)
        for response in results:
            if response.is_successful:
                success += 1
        failed -= success

        return success, failed
