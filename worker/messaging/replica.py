import asyncio
import dataclasses
import multiprocessing
from typing import Dict

import aioredis

from common.logger.logger import get_logger
from common.queue.messaging import blocking_get_messaging_job
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
    REDIS_TIMEOUT = 0  # Infinite

    def __init__(self, pid):
        loop = asyncio.get_event_loop()

        redis_host = config.push_worker.redis.host
        redis_port = config.push_worker.redis.port
        redis_password = config.push_worker.redis.password
        self.redis_pool = loop.run_until_complete(
            aioredis.create_pool(
                f'redis://{redis_host}:{redis_port}',
                password=redis_password,
                db=int(config.push_worker.redis.notification_queue.database),
                minsize=5,
                maxsize=10,
            )
        )

        fcm: AbstractFCM = self.create_fcm_client()
        apns: AbstractAPNs = self.create_apns_client()
        self.tasks: Dict[MessagingTask, AbstractTask] = {
            MessagingTask.SEND_PUSH_MESSAGE: SendPushMessageTask(
                fcm=fcm,
                apns=apns,
                redis_pool=self.redis_pool,
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
            with await self.redis_pool as redis_conn:
                job = await blocking_get_messaging_job(
                    redis_conn=redis_conn,
                    timeout=self.REDIS_TIMEOUT
                )
                logger.debug(multiprocessing.current_process())

                if not job:
                    continue

                logger.info('new task')
                asyncio.create_task(self.process_job(job))
