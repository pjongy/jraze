import dataclasses
import enum
from typing import List, Optional

import deserialize
import httpx

from batch.notification.config import config
from batch.notification.exception.external import ExternalException
from common.logger.logger import get_logger
from common.structure.condition import ConditionClause

logger = get_logger(__name__)


class NotificationStatus(enum.IntEnum):
    DRAFT = 0
    LAUNCHED = 1
    SENT = 2
    ERROR = 3
    DELETED = 4
    QUEUED = 5


@dataclasses.dataclass
class Notification:
    id: int
    uuid: str
    title: str
    body: str
    deep_link: Optional[str]
    image_url: Optional[str]
    icon_url: Optional[str]
    conditions: dict
    status: NotificationStatus


@dataclasses.dataclass
class GetLaunchedNotificationsResponse:
    @dataclasses.dataclass
    class Result:
        total: int
        notifications: List[Notification]

    result: Result


@dataclasses.dataclass
class UpdateNotificationStatusResponse:
    result: Notification


class JrazeApi:
    JRAZE_BASE_URL = config.notification_batch.external.jraze.base_url
    X_SERVER_KEY = config.notification_batch.external.jraze.x_server_key

    async def get_launched_notifications(
        self,
        start: int,
        size: int,
    ) -> GetLaunchedNotificationsResponse:
        LAUNCHED_NOTIFICATION_PATH = 'notifications/-/launched'
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=f'{self.JRAZE_BASE_URL}{LAUNCHED_NOTIFICATION_PATH}',
                params={
                    'start': start,
                    'size': size,
                },
            )
            if not 200 <= response.status_code < 300:
                logger.error(f'launched notification error: {response.read()}')
                raise ExternalException()

            return deserialize.deserialize(GetLaunchedNotificationsResponse, response.json())

    async def get_filtered_device_total(
        self,
        condition_clause: ConditionClause,
    ) -> int:
        SEARCH_DEVICES_PATH = 'devices/-/:search'
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f'{self.JRAZE_BASE_URL}{SEARCH_DEVICES_PATH}',
                json={
                    'conditions': dataclasses.asdict(condition_clause),
                    'start': 0,
                    'size': 1,
                },
            )
            if not 200 <= response.status_code < 300:
                logger.error(f'device search error: {response.read()}')
                raise ExternalException()

            return response.json()['result']['total']

    async def update_notification_status(
        self,
        notification_uuid: str,
        status: NotificationStatus
    ) -> UpdateNotificationStatusResponse:
        UPDATE_NOTIFICATION_STATUS_PATH = f'notifications/{notification_uuid}/status'
        async with httpx.AsyncClient() as client:
            response = await client.put(
                url=f'{self.JRAZE_BASE_URL}{UPDATE_NOTIFICATION_STATUS_PATH}',
                json={'status': status},
            )
            if not 200 <= response.status_code < 300:
                logger.error(f'update notification status error: {response.read()}')
                raise ExternalException()

            return deserialize.deserialize(UpdateNotificationStatusResponse, response.json())
