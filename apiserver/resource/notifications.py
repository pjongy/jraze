from typing import List, Optional

import deserialize

from apiserver.decorator.request import request_error_handler
from apiserver.repository.notification import find_notifications_by_status, \
    notification_model_to_dict
from apiserver.resource import json_response, convert_request
from common.logger.logger import get_logger
from common.model.notification import NotificationStatus

logger = get_logger(__name__)


@deserialize.default('status', None)
@deserialize.default('start', 0)
@deserialize.default('start', 10)
@deserialize.default('order_bys', [])
class FetchNotificationsRequest:
    status: Optional[NotificationStatus]
    start: int
    size: int
    order_bys: List[str]


class NotificationsHttpResource:
    def __init__(self, router, storage, secret, external):
        self.router = router

    def route(self):
        self.router.add_route('GET', '', self.get_notifications)

    @request_error_handler
    async def get_notifications(self, request):
        query_params: FetchNotificationsRequest = convert_request(
            FetchNotificationsRequest,
            request.rel_url.query,
        )

        total, notifications = find_notifications_by_status(
            status=query_params.status,
            start=query_params.start,
            size=query_params.size,
            order_bys=query_params.order_bys,
        )

        return json_response(result={
            'total': total,
            'notifications': [
                notification_model_to_dict(notification)
                for notification in notifications
            ]
        })
