import asyncio
import dataclasses
from typing import Dict, List

import aiomysql
import deserialize
from jasyncq.dispatcher.tasks import TasksDispatcher
from jasyncq.dispatcher.model.task import TaskOut
from jasyncq.repository.tasks import TaskRepository

from common.logger.logger import get_logger
from common.structure.job.messaging import MessagingJob, MessagingTask
from worker.messaging.config import config
from worker.messaging.external.apns.abstract import AbstractAPNs
from worker.messaging.external.apns.v3 import APNsV3
from worker.messaging.external.fcm.abstract import AbstractFCM
from worker.messaging.external.fcm.legacy import FCMClientLegacy
from worker.messaging.external.fcm.v1 import FCMClientV1
from worker.messaging.task import AbstractTask
from worker.messaging.task.send_push_message import SendPushMessageTask

logger = get_logger(__name__)


class Replica:
    MESSAGING_QUEUE = 'MESSAGING_QUEUE'
    TASK_FETCH_SIZE = 1

    def __init__(self, pid):
        loop = asyncio.get_event_loop()

        task_queue_config = config.push_worker.task_queue
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

        messaging_task_queue_repository = TaskRepository(
            pool=self.task_queue_pool,
            topic_name='MESSAGING_TOPIC',
        )
        loop.run_until_complete(messaging_task_queue_repository.initialize())
        self.messaging_task_queue = TasksDispatcher(
            repository=messaging_task_queue_repository,
        )

        notification_queue_repository = TaskRepository(
            pool=self.task_queue_pool,
            topic_name='NOTIFICATION_TOPIC',
        )
        loop.run_until_complete(notification_queue_repository.initialize())
        notification_queue_dispatcher = TasksDispatcher(
            repository=notification_queue_repository
        )

        fcm: AbstractFCM = self.create_fcm_client()
        apns: AbstractAPNs = self.create_apns_client()
        self.tasks: Dict[MessagingTask, AbstractTask] = {
            MessagingTask.SEND_PUSH_MESSAGE: SendPushMessageTask(
                fcm=fcm,
                apns=apns,
                notification_task_queue=notification_queue_dispatcher,
            )
        }

        logger.debug(f'Worker {pid} up')
        loop.run_until_complete(self.job())

    def create_apns_client(self) -> AbstractAPNs:
        apns_config = config.push_worker.apns
        return APNsV3(
            p8_filename=apns_config.p8_cert.file_name,
            p8_key_id=apns_config.p8_cert.key_id,
            p8_team_id=apns_config.p8_cert.team_id,
            p8_topic=apns_config.p8_cert.topic,
            pem_client_cert=apns_config.pem_cert.file_name,
            cert_type=apns_config.cert_type,
        )

    def create_fcm_client(self) -> AbstractFCM:
        fcm_config = config.push_worker.fcm
        if config.push_worker.fcm.client == 'legacy':
            return FCMClientLegacy(fcm_config.legacy.server_key)
        elif config.push_worker.fcm.client == 'v1':
            return FCMClientV1(fcm_config.v1.project_id, fcm_config.v1.key_file_name)
        else:
            raise ValueError(f'fcm client not allow: {config.push_worker.fcm.client}')

    async def process_job(self, job: MessagingJob):  # real worker if job published
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
            pending_tasks = await self.messaging_task_queue.fetch_pending_tasks(
                queue_name=self.MESSAGING_QUEUE,
                limit=self.TASK_FETCH_SIZE,
                check_term_seconds=60,
            )
            scheduled_tasks = await self.messaging_task_queue.fetch_scheduled_tasks(
                queue_name=self.MESSAGING_QUEUE,
                limit=self.TASK_FETCH_SIZE,
            )

            tasks: List[TaskOut] = [*pending_tasks, *scheduled_tasks]
            if not tasks:
                # NOTE(pjongy): Relax wasting
                await asyncio.sleep(1)

            await asyncio.gather(*[
                self.process_job(job=deserialize.deserialize(MessagingJob, task.task))
                for task in tasks
            ])
            task_ids = [str(task.uuid) for task in tasks]
            if task_ids:
                await self.messaging_task_queue.complete_tasks(task_ids=task_ids)
