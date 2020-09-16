import deserialize
from aioredis import ConnectionsPool

from common.logger.logger import get_logger
from common.queue.result.push import publish_push_result_job
from common.structure.job.messaging import SendPushMessageArgs, SendPlatform
from common.structure.job.result import ResultJob
from worker.messaging.external.apns.abstract import AbstractAPNs
from worker.messaging.external.fcm.abstract import AbstractFCM
from worker.messaging.task import AbstractTask

logger = get_logger(__name__)


class SendPushMessageTask(AbstractTask):
    def __init__(self, fcm: AbstractFCM, apns: AbstractAPNs, redis_pool: ConnectionsPool):
        self.fcm: AbstractFCM = fcm
        self.apns: AbstractAPNs = apns
        self.redis_pool: ConnectionsPool = redis_pool

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
            logger.info(f'sent: {sent}, failed: {failed}')
            await self._publish_job_to_result_queue(
                result_job=deserialize.deserialize(ResultJob, {
                    'id': task_args.notification_id,
                    'sent': sent,
                    'device_platform': task_args.device_platform,
                    'failed': failed,
                })
            )
        elif task_args.send_platform == SendPlatform.APNS:
            sent, failed = await self.apns.send_data(
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
            await self._publish_job_to_result_queue(
                result_job=deserialize.deserialize(ResultJob, {
                    'id': task_args.notification_id,
                    'sent': sent,
                    'device_platform': task_args.device_platform,
                    'failed': failed,
                })
            )
        else:
            raise NotImplementedError(
                f'Can not handle SendPlatform type {task_args.send_platform.name}')

    async def _publish_job_to_result_queue(self, result_job: ResultJob):
        with await self.redis_pool as redis_conn:
            pushed_job_count = await publish_push_result_job(
                redis_conn=redis_conn,
                job=result_job
            )
            return pushed_job_count
