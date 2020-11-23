from typing import List

from aiohttp.web_request import Request

from apiserver.decorator.internal import restrict_external_request_handler
from apiserver.decorator.request import request_error_handler
from apiserver.exception.permission import ServerKeyError
from apiserver.repository.device_notification_log import add_device_notification_logs
from apiserver.repository.notification import increase_sent_count, change_notification_status, \
    find_notification_by_id
from apiserver.resource import json_response, convert_request
from apiserver.resource.abstract import AbstractResource
from common.logger.logger import get_logger
from apiserver.model.notification import NotificationStatus

logger = get_logger(__name__)


class CreateDeviceNotificationLogRequest:
    device_ids: List[int]
    notification_id: int


class IncreaseNotificationSentAmountRequest:
    ios: int
    android: int


class InternalHttpResource(AbstractResource):
    def __init__(self, internal_api_keys: List[str]):
        super().__init__(logger=logger)
        self.router = self.app.router
        self.internal_api_keys = internal_api_keys

    def _check_server_key(self, request: Request):
        x_server_key = request.headers.get('X-Server-Key')
        if x_server_key not in self.internal_api_keys:
            raise ServerKeyError()

    def route(self):
        self.router.add_route(
            'POST', '/devices/logs/notification:add', self.create_device_notification_log)
        self.router.add_route(
            'POST', '/notifications/{notification_uuid}/sent:increase',
            self.increase_notification_sent_result)

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

    @request_error_handler
    @restrict_external_request_handler
    async def increase_notification_sent_result(self, request):
        self._check_server_key(request)

        notification_uuid = request.match_info['notification_uuid']

        request_body: IncreaseNotificationSentAmountRequest = convert_request(
            IncreaseNotificationSentAmountRequest, await request.json())
        notification = await find_notification_by_id(uuid=notification_uuid)

        if notification is None:
            return json_response(reason=f'notification not found {notification_uuid}', status=404)

        if notification.status == NotificationStatus.DRAFT:
            await change_notification_status(
                target_notification=notification,
                status=NotificationStatus.SENT,
            )

        await increase_sent_count(
            uuid_=notification_uuid,
            sent_android=request_body.android,
            sent_ios=request_body.ios,
        )
        return json_response(result={
            'android': request_body.android,
            'ios': request_body.ios,
        })
