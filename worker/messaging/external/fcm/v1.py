import asyncio
from typing import List, Tuple

import google.auth
import google.auth.transport.requests
import httpx
from google.oauth2.service_account import Credentials
from httpx import Response

from common.logger.logger import get_logger
from worker.messaging.external.fcm.abstract import AbstractFCM

logger = get_logger(__name__)


class FCMClientV1(AbstractFCM):
    FCM_BASE_URL = 'https://fcm.googleapis.com/v1/projects/'
    SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']

    def __init__(self, project_id: str, service_account_file_name: str):
        self.project_id = project_id
        self.credential: Credentials = Credentials.from_service_account_file(
            service_account_file_name,
            scopes=self.SCOPES
        )

    def get_access_token(self):
        if self.credential.expiry is None or self.credential.expired:
            self.credential.refresh(google.auth.transport.requests.Request())
        return self.credential.token

    async def send_data(
        self,
        targets: List[str],
        data: dict
    ) -> Tuple[int, int]:
        PUSH_SEND_PATH = f'{self.project_id}/messages:send'
        async with httpx.AsyncClient() as client:
            results: List[Response] = await asyncio.gather(*[
                client.post(
                    url=f'{self.FCM_BASE_URL}{PUSH_SEND_PATH}',
                    json={
                        "message": {
                            "token": target,
                            **data
                        }
                    },
                    headers={
                        'Authorization': f'Bearer {self.get_access_token()}'
                    }
                )
                for target in targets
            ])

            success = 0
            failed = len(targets)
            for response in results:
                logger.debug(response)
                if not 200 <= response.status_code < 300:
                    logger.error(f'fcm data sent failed {response}')

                if 'name' in response.json():
                    success += 1
            failed -= success

            return success, failed
