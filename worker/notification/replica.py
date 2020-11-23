import asyncio
import dataclasses
from typing import Dict, List

import aiomysql
import deserialize
from jasyncq.dispatcher.tasks import TasksDispatcher
from jasyncq.model.task import Task
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
        loop = asyncio.get_event_loop()

        task_queue_config = config.notification_worker.task_queue
        self.task_queue_pool = loop.run_until_complete(
            aiomysql.create_pool(
                host=task_queue_config.host,
                port=task_queue_config.port,
                user=task_queue_config.user,
                password=task_queue_config.password,
                db=task_queue_config.database,
                loop=loop,
                autocommit=False,
            )
        )
        notification_queue_repository = TaskRepository(
            pool=self.task_queue_pool,
            topic_name='NOTIFICATION_TOPIC',
        )
        loop.run_until_complete(notification_queue_repository.initialize())
        self.notification_queue_dispatcher = TasksDispatcher(
            repository=notification_queue_repository
        )
        self.jraze_api = JrazeApi()

        messaging_task_queue_repository = TaskRepository(
            pool=self.task_queue_pool,
            topic_name='MESSAGING_TOPIC',
        )
        loop.run_until_complete(messaging_task_queue_repository.initialize())
        messaging_task_queue = TasksDispatcher(
            repository=messaging_task_queue_repository,
        )
        self.tasks: Dict[NotificationTask, AbstractTask] = {
            NotificationTask.LAUNCH_NOTIFICATION: LaunchNotificationTask(
                jraze_api=self.jraze_api,
                messaging_task_queue=messaging_task_queue,
            ),
            NotificationTask.UPDATE_RESULT: UpdatePushResultTask(
                jraze_api=self.jraze_api,
            ),
        }
        logger.debug(f'Worker {pid} up')
        loop.run_until_complete(self.job())

    async def process_job(self, job: NotificationJob):  # real worker if job published
        try:
            logger.debug(job)
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

            tasks: List[Task] = [*pending_tasks, *scheduled_tasks]
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
