import asyncio
import uuid
from typing import List, Tuple

import httpx
from httpx import Response

from common.logger.logger import get_logger
from worker.push.apns.auth.jwt import AppleJWT

logger = get_logger(__name__)


class APNsV3:
    APNS_BASE_URL = 'https://api.push.apple.com'

    def __init__(self, apple_jwt: AppleJWT):
        self.apple_jwt: AppleJWT = apple_jwt
        self.access_token = None

    def generate_access_token(self) -> str:
        return self.apple_jwt.generate()

    async def send_data(
        self,
        targets: List[str],
        data: dict
    ) -> Tuple[int, int]:
        collapse_id = str(uuid.uuid4())
        async with httpx.AsyncClient(http2=True) as client:
            results = await asyncio.gather(*[
                client.post(
                    url=f'{self.APNS_BASE_URL}/3/device/{target}',
                    json={
                        'aps': data
                    },
                    headers={
                        'authorization': f'bearer {self.generate_access_token()}',
                        'apns-collapse-id': collapse_id
                    }
                ) for target in targets
            ])

        success = 0
        failed = len(targets)
        for result in results:
            result: Response = result
            response = result.json()
            logger.debug(response)
            if not 200 <= result.status_code < 300:
                logger.error(f'apns data sent failed {response}')
                continue

            success += 1
        failed -= success

        return success, failed
