from typing import List

from aiohttp.web_request import Request

from apiserver.decorator.internal import restrict_external_request_handler
from apiserver.decorator.request import request_error_handler
from apiserver.exception.permission import ServerKeyError
from apiserver.repository.device_notification_log import add_device_notification_logs
from apiserver.resource import json_response, convert_request
from common.logger.logger import get_logger

logger = get_logger(__name__)


class CreateDeviceNotificationLogRequest:
    device_ids: List[int]
    notification_id: int


class InternalHttpResource:
    def __init__(self, router, storage, secret, external):
        self.router = router
        self.internal_api_keys: List[str] = secret['internal_api_keys']

    def _check_server_key(self, request: Request):
        x_server_key = request.headers.get('X-Server-Key')
        if x_server_key not in self.internal_api_keys:
            raise ServerKeyError()

    def route(self):
        self.router.add_route(
            'POST', '/devices/logs/notification:add', self.create_device_notification_log)

    @request_error_handler
    @restrict_external_request_handler
    async def create_device_notification_log(self, request):
        self._check_server_key(request)

        request_body: CreateDeviceNotificationLogRequest = convert_request(
            CreateDeviceNotificationLogRequest, await request.json())

        await add_device_notification_logs(
            device_ids=request_body.device_ids,
            notification_id=request_body.notification_id,
        )
        return json_response(result=len(request_body.device_ids))
