from typing import List, Tuple

import httpx

from common.logger.logger import get_logger
from worker.messaging.fcm.external.fcm.abstract import AbstractFCM

logger = get_logger(__name__)


class FCMClientLegacy(AbstractFCM):
    FCM_API_HOST = 'https://fcm.googleapis.com'

    def __init__(self, server_key):
        self.server_key = server_key

    async def send_data(
        self,
        targets: List[str],
        data: dict
    ) -> Tuple[int, int]:
        PUSH_SEND_PATH = '/fcm/send'
        body = {
            **data,
            "registration_ids": targets
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f'{self.FCM_API_HOST}{PUSH_SEND_PATH}',
                json=body,
                headers={'Authorization': f'key={self.server_key}'}
            )
            logger.debug(response)

            if not 200 <= response.status_code < 300:
                raise PermissionError(f'fcm data sent failed {response}')

            result = response.json()
            return result['success'], result['failure']
