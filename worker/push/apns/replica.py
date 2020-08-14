import asyncio
import json
import multiprocessing
from typing import List, Tuple
from uuid import uuid4

import aioredis
import deserialize
from aioapns import APNs, NotificationRequest, PushType

from common.logger.logger import get_logger
from common.queue.push.apns import blocking_get_apns_job
from common.queue.result.push import publish_push_result_job
from common.structure.job.apns import APNsJob
from worker.push.apns.config import config

logger = get_logger(__name__)


class Replica:
    REDIS_TIMEOUT = 0  # Infinite

    def __init__(self, pid):
        self.apns = self.create_apns()
        self.redis_host = config.push_worker.redis.host
        self.redis_port = config.push_worker.redis.port
        self.redis_password = config.push_worker.redis.password
        self.redis_pool = None

        logger.debug(f'Worker {pid} up')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.job())

    def create_apns(self) -> APNs:
        apns_config = config.push_worker.apns
        args = {
            'pem': {
                'client_cert': apns_config.pem_cert.file_name
            },
            'p8': {
                'key': apns_config.p8_cert.file_name,
                'key_id': apns_config.p8_cert.key_id,
                'team_id': apns_config.p8_cert.team_id,
                'topic': apns_config.p8_cert.topic,
            }
        }[apns_config.cert_type]
        print(args)
        return APNs(
            use_sandbox=False,
            **args
        )

    async def _send_notification(self, targets: List[str], data: dict) -> Tuple[int, int]:
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

    async def process_job(self, job_json):  # real worker if job published
        try:
            logger.debug(job_json)
            job: APNsJob = deserialize.deserialize(
                APNsJob, json.loads(job_json)
            )
            if not job.device_tokens:
                return

            sent, failed = await self._send_notification(
                targets=job.device_tokens,
                data={
                    'aps': {
                        'alert': {
                            'title': job.title,
                            'body': job.body,
                        }
                    }
                }
            )
            logger.info(f'sent: {sent}, failed: {failed}')

            if job.id:
                with await self.redis_pool as redis_conn:
                    await publish_push_result_job(
                        redis_conn=redis_conn,
                        job={
                            'id': job.id,
                            'sent': sent,
                            'failed': failed,
                        }
                    )
        except Exception:
            logger.exception(f'Fatal Error! {job_json}')

    async def job(self):  # real working job
        self.redis_pool = await aioredis.create_pool(
            f'redis://{self.redis_host}:{self.redis_port}',
            password=self.redis_password,
            db=int(config.push_worker.redis.notification_queue.database),
            minsize=5,
            maxsize=10,
        )
        while True:
            with await self.redis_pool as redis_conn:
                job_json = await blocking_get_apns_job(
                    redis_conn=redis_conn,
                    timeout=self.REDIS_TIMEOUT
                )
                logger.debug(multiprocessing.current_process())

                if not job_json:
                    continue

                logger.info('new task')
                asyncio.create_task(self.process_job(job_json))
