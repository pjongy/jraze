import asyncio
import dataclasses
from typing import Dict, List

import aiomysql
import deserialize
from jasyncq.dispatcher.tasks import TasksDispatcher
from jasyncq.dispatcher.model.task import TaskOut
from jasyncq.repository.tasks import TaskRepository

from common.logger.logger import get_logger
from common.structure.job.notification import NotificationJob, NotificationTask
from worker.notification.config import config
from worker.notification.external.jraze.jraze import JrazeApi
from worker.notification.task import AbstractTask
from worker.notification.task.launch_notification import LaunchNotificationTask
from worker.notification.task.update_push_result import UpdatePushResultTask

logger = get_logger(__name__)


class Replica:
    NOTIFICATION_JOB_QUEUE = 'NOTIFICATION_JOB_QUEUE'
    TASK_FETCH_SIZE = 300

    def __init__(self, pid):
        task_queue_config = config.notification_worker.task_queue
        self.jraze_api = JrazeApi()

        loop = asyncio.get_event_loop()
        self.notification_queue_dispatcher = loop.run_until_complete(self._get_task_dispatcher(
            task_queue_config=task_queue_config,
            topic='NOTIFICATION_TOPIC',
        ))
        apns_messaging_task_queue = loop.run_until_complete(self._get_task_dispatcher(
            task_queue_config=task_queue_config,
            topic='APNS_MESSAGING_TOPIC',
        ))
        fcm_messaging_task_queue = loop.run_until_complete(self._get_task_dispatcher(
            task_queue_config=task_queue_config,
            topic='FCM_MESSAGING_TOPIC',
        ))

        self.tasks: Dict[NotificationTask, AbstractTask] = {
            NotificationTask.LAUNCH_NOTIFICATION: LaunchNotificationTask(
                jraze_api=self.jraze_api,
                apns_messaging_task_queue=apns_messaging_task_queue,
                fcm_messaging_task_queue=fcm_messaging_task_queue,
            ),
            NotificationTask.UPDATE_RESULT: UpdatePushResultTask(
                jraze_api=self.jraze_api,
            ),
        }
        logger.info(f'Worker {pid} up')
        loop.run_until_complete(self.job())

    async def _get_task_dispatcher(
        self,
        task_queue_config: config.NotificationWorker.MySQL,
        topic: str,
    ) -> TasksDispatcher:
        task_queue_pool = await aiomysql.create_pool(
            host=task_queue_config.host,
            port=task_queue_config.port,
            user=task_queue_config.user,
            password=task_queue_config.password,
            db=task_queue_config.database,
            autocommit=False,
        )
        notification_queue_repository = TaskRepository(
            pool=task_queue_pool,
            topic_name=topic,
        )
        await notification_queue_repository.initialize()
        return TasksDispatcher(
            repository=notification_queue_repository
        )

    async def process_job(self, job: NotificationJob):  # real worker if job published
        try:
            logger.info(job)
            try:
                task = self.tasks[job.task]
            except KeyError as e:
                logger.warning(f'unknown task({job.task.name}): {e}')
                return

            await task.run(kwargs=job.kwargs)
        except Exception:
            logger.exception(f'Fatal Error! {dataclasses.asdict(job)}')

    async def job(self):  # real working job
        while True:
            pending_tasks = await self.notification_queue_dispatcher.fetch_pending_tasks(
                queue_name=self.NOTIFICATION_JOB_QUEUE,
                limit=self.TASK_FETCH_SIZE,
                check_term_seconds=60,
            )
            scheduled_tasks = await self.notification_queue_dispatcher.fetch_scheduled_tasks(
                queue_name=self.NOTIFICATION_JOB_QUEUE,
                limit=self.TASK_FETCH_SIZE,
            )

            tasks: List[TaskOut] = [*pending_tasks, *scheduled_tasks]
            if not tasks:
                # NOTE(pjongy): Relax wasting
                await asyncio.sleep(1)

            await asyncio.gather(*[
                self.process_job(job=deserialize.deserialize(NotificationJob, task.task))
                for task in tasks
            ])
            task_ids = [str(task.uuid) for task in tasks]
            if task_ids:
                await self.notification_queue_dispatcher.complete_tasks(task_ids=task_ids)
