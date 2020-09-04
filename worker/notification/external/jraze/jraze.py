from typing import List, Optional

import deserialize
import httpx

from common.structure.enum import DevicePlatform, SendPlatform
from worker.notification.config import config
from common.logger.logger import get_logger
from worker.notification.exception.external import ExternalException

logger = get_logger(__name__)


class SearchDeviceResponse:
    class Result:
        class Device:
            id: int
            external_id: str
            push_token: str
            send_platform: SendPlatform
            device_platform: DevicePlatform
            created_at: str
            modified_at: Optional[str]
            device_properties: List[dict]
        total: int
        devices: List[Device]
    result: Result


class LogNotificationResponse:
    result: int


class JrazeApi:
    JRAZE_BASE_URL = config.notification_worker.external.jraze.base_url
    X_SERVER_KEY = config.notification_worker.external.jraze.x_server_key

    async def log_notification(
        self,
        device_ids: List[int],
        notification_id: int,
    ) -> LogNotificationResponse:
        NOTIFICATION_LOG_PATH = 'internal/devices/logs/notification:add'
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f'{self.JRAZE_BASE_URL}{NOTIFICATION_LOG_PATH}',
                json={
                    'device_ids': device_ids,
                    'notification_id': notification_id,
                },
                headers={
                    'X-Server-Key': self.X_SERVER_KEY,
                }
            )
            if not 200 <= response.status_code < 300:
                logger.error(f'device notification log error: {response.read()}')
                raise ExternalException()

            return deserialize.deserialize(LogNotificationResponse, response.json())

    async def search_devices(
        self,
        conditions: dict,
        start: int,
        size: int,
    ) -> SearchDeviceResponse:
        print(self.X_SERVER_KEY)
        SEARCH_DEVICES_PATH = 'devices/-/:search'
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f'{self.JRAZE_BASE_URL}{SEARCH_DEVICES_PATH}',
                json={
                    'conditions': conditions,
                    'start': start,
                    'size': size,
                },
                headers={
                    'X-Server-Key': self.X_SERVER_KEY,
                }
            )
            if not 200 <= response.status_code < 300:
                logger.error(f'device notification log error: {response.read()}')
                raise ExternalException()

            return deserialize.deserialize(SearchDeviceResponse, response.json())
