import asyncio
from typing import List, Tuple
from uuid import uuid4

from aioapns import APNs, NotificationRequest, PushType

from worker.messaging.apns.external.apns.abstract import AbstractAPNs


class APNsV3(AbstractAPNs):
    def __init__(
        self,
        p8_filename: str = '',
        p8_key_id: str = '',
        p8_team_id: str = '',
        p8_topic: str = '',
        pem_client_cert: str = '',
        cert_type: str = '',
    ):
        args = {
            'pem': {
                'client_cert': pem_client_cert
            },
            'p8': {
                'key': p8_filename,
                'key_id': p8_key_id,
                'team_id': p8_team_id,
                'topic': p8_topic,
            }
        }[cert_type]
        self.apns = APNs(
            use_sandbox=False,
            **args
        )

    async def send_data(
        self,
        targets: List[str],
        data: dict
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
