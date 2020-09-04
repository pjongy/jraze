import deserialize
import httpx

from worker.result.config import config
from common.logger.logger import get_logger
from worker.result.exception.external import ExternalException

logger = get_logger(__name__)


class IncreaseNotificationSentResponse:
    class Result:
        ios: int
        android: int
    result: Result


class JrazeApi:
    JRAZE_BASE_URL = config.result_worker.external.jraze.base_url
    X_SERVER_KEY = config.result_worker.external.jraze.x_server_key

    async def increase_notification_sent(
        self,
        notification_uuid: str,
        ios: int = 0,
        android: int = 0,
    ) -> IncreaseNotificationSentResponse:
        INCREASE_PATH = f'internal/notifications/{notification_uuid}/sent:increase'
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=f'{self.JRAZE_BASE_URL}{INCREASE_PATH}',
                json={
                    'ios': ios,
                    'android': android,
                },
                headers={
                    'X-Server-Key': self.X_SERVER_KEY,
                }
            )
            if not 200 <= response.status_code < 300:
                logger.error(f'increase notification sent amount log error: {response.read()}')
                raise ExternalException()

            return deserialize.deserialize(IncreaseNotificationSentResponse, response.json())
