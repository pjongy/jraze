import asyncio
import dataclasses
import math

import aioredis
import deserialize

from common.logger.logger import get_logger
from common.queue.notification import publish_notification_job
from common.structure.condition import ConditionClause
from common.structure.job.notification import NotificationJob, NotificationTask
from batch.notification.config import config
from batch.notification.external.jraze.jraze import JrazeApi, Notification, NotificationStatus

logger = get_logger(__name__)


class Replica:
    FETCHING_SIZE = 300
    NOTIFICATION_WORKER_COUNT = int(config.notification_batch.notification_worker.worker_count)
    WORK_TERM_IN_SECONDS = int(config.notification_batch.work_term)

    def __init__(self):
        loop = asyncio.get_event_loop()

        redis_host = config.notification_batch.redis.host
        redis_port = config.notification_batch.redis.port
        redis_password = config.notification_batch.redis.password
        self.redis_pool = loop.run_until_complete(
            aioredis.create_pool(
                f'redis://{redis_host}:{redis_port}',
                password=redis_password,
                db=int(config.notification_batch.redis.notification_queue.database),
                minsize=5,
                maxsize=10,
            )
        )

        self.jraze_api = JrazeApi()
        loop.run_until_complete(self.job())

    async def publish_notification_jobs(self, notification: Notification):
        conditions = deserialize.deserialize(ConditionClause, notification.conditions)
        device_total = await self.jraze_api.get_filtered_device_total(
            condition_clause=conditions,
        )
        notification_job_capacity = math.ceil(device_total / self.NOTIFICATION_WORKER_COUNT)

        try:
            tasks = []
            with await self.redis_pool as redis_conn:
                for job_index in range(self.NOTIFICATION_WORKER_COUNT):
                    job: NotificationJob = deserialize.deserialize(
                        NotificationJob, {
                            'task': NotificationTask.LAUNCH_NOTIFICATION,
                            'kwargs': {
                                'notification': {
                                    'id': notification.id,
                                    'uuid': str(notification.uuid),
                                    'title': notification.title,
                                    'body': notification.body,
                                    'image_url': notification.image_url,
                                    'icon_url': notification.icon_url,
                                    'deep_link': notification.deep_link,
                                },
                                'conditions': dataclasses.asdict(conditions),
                                'device_range': {
                                    'start': job_index * notification_job_capacity,
                                    'size': notification_job_capacity,
                                },
                            },
                        }
                    )
                    tasks.append(
                        publish_notification_job(
                            redis_conn=redis_conn,
                            job=job,
                        )
                    )
                await asyncio.gather(*tasks)
        except Exception as e:  # rollback if queue pushing failed
            logger.warning(f'rollback because of queue pushing failed {e}')
            response = await self.jraze_api.update_notification_status(
                notification_uuid=notification.uuid,
                status=NotificationStatus.ERROR,
            )
            logger.warning(
                f'notification ({response.result.uuid}) status updated: {response.result.status}')
        response = await self.jraze_api.update_notification_status(
            notification_uuid=notification.uuid,
            status=NotificationStatus.QUEUED,
        )
        logger.debug(
            f'notification ({response.result.uuid}) status updated: {response.result.status}')

    async def job(self):  # real working job
        while True:

            start = 0
            while True:
                response = await self.jraze_api.get_launched_notifications(
                    start=start,
                    size=self.FETCHING_SIZE,
                )
                start += self.FETCHING_SIZE

                await asyncio.gather(*[
                    self.publish_notification_jobs(notification)
                    for notification in response.result.notifications
                ])

                if response.result.total <= start:
                    break
            await asyncio.sleep(self.WORK_TERM_IN_SECONDS)
