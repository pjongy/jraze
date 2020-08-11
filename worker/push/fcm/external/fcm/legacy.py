from typing import List, Tuple

from common.logger.logger import get_logger
from common.request import Request
from worker.push.fcm.external.fcm.abstract import AbstractFCM

logger = get_logger(__name__)


class FCMClientLegacy(Request, AbstractFCM):
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
        status, response, _ = await self.post(
            url=f'{self.FCM_API_HOST}{PUSH_SEND_PATH}',
            parameters=body,
            headers={'Authorization': f'key={self.server_key}'}
        )
        logger.debug(response)

        if not 200 <= status < 300:
            raise PermissionError(f'fcm data sent failed {response}')

        return response['success'], response['failure']
