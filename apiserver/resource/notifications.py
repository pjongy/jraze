import datetime
from typing import List, Optional

import deserialize

from apiserver.decorator.request import request_error_handler
from apiserver.repository.notification import find_notifications_by_status, \
    notification_model_to_dict, find_notification_by_id, create_notification
from apiserver.resource import json_response, convert_request
from common.logger.logger import get_logger
from common.model.notification import NotificationStatus
from common.structure.condition import ConditionClause
from common.util import string_to_utc_datetime, object_to_dict

logger = get_logger(__name__)


@deserialize.default('start', 0)
@deserialize.default('size', 10)
@deserialize.default('order_bys', [])
@deserialize.parser('order_bys', lambda arg: arg.split(','))  # comma separated string to list
class FetchNotificationsRequest:
    status: Optional[NotificationStatus]
    start: int
    size: int
    order_bys: List[str]


@deserialize.parser('scheduled_at', string_to_utc_datetime)
class CreateNotificationRequest:
    title: str
    body: str
    image_url: Optional[str]
    icon_url: Optional[str]
    deep_link: Optional[str]
    conditions: Optional[dict]
    scheduled_at: Optional[datetime.datetime]


class NotificationsHttpResource:
    def __init__(self, router, storage, secret, external):
        self.router = router

    def route(self):
        self.router.add_route('GET', '', self.get_notifications)
        self.router.add_route('POST', '', self.create_notification)
        self.router.add_route('GET', '/{notification_id}', self.get_notification)

    @request_error_handler
    async def get_notifications(self, request):
        query_params: FetchNotificationsRequest = convert_request(
            FetchNotificationsRequest,
            dict(request.rel_url.query),
        )
        available_order_by_fields = {
            'created_at', '-created_at',
            'modified_at', '-modified_at',
            'scheduled_at', '-scheduled_at',
        }

        total, notifications = await find_notifications_by_status(
            status=query_params.status,
            start=query_params.start,
            size=query_params.size,
            order_bys=list(available_order_by_fields.intersection(query_params.order_bys)),
        )

        return json_response(result={
            'total': total,
            'notifications': [
                notification_model_to_dict(notification)
                for notification in notifications
            ]
        })

    @request_error_handler
    async def get_notification(self, request):
        notification_id = request.match_info['notification_id']
        notification = await find_notification_by_id(_id=notification_id)

        return json_response(result=notification_model_to_dict(notification))

    @request_error_handler
    async def create_notification(self, request):
        request: CreateNotificationRequest = convert_request(
            CreateNotificationRequest,
            await request.json(),
        )

        conditions = {}
        try:
            conditions = object_to_dict(
                deserialize.deserialize(ConditionClause, request.conditions)
            )
        except deserialize.exceptions.DeserializeException as error:
            json_response(reason=f'wrong condition clause {error}', status=400)

        notification = await create_notification(
            title=request.title,
            body=request.body,
            deep_link=request.deep_link,
            image_url=request.image_url,
            icon_url=request.icon_url,
            conditions=conditions,
            scheduled_at=request.scheduled_at,
        )
        return json_response(result=notification_model_to_dict(notification))
