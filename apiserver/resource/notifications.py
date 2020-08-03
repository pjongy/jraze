import asyncio
import datetime
import math
from typing import List, Optional

import deserialize
from aioredis import ConnectionsPool

from apiserver.config import config
from apiserver.decorator.request import request_error_handler
from apiserver.repository.device import get_device_total_by_conditions
from apiserver.repository.notification import find_notifications_by_status, \
    notification_model_to_dict, find_notification_by_id, create_notification, \
    change_notification_status
from apiserver.resource import json_response, convert_request
from common.logger.logger import get_logger
from common.model.notification import NotificationStatus
from common.queue.notification import publish_notification_job
from common.structure.condition import ConditionClause
from common.structure.job.notification import NotificationJob
from common.util import string_to_utc_datetime, object_to_dict, utc_now

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
    NOTIFICATION_JOB_QUEUE_TOPIC = 'NOTIFICATION_JOB_QUEUE'
    NOTIFICATION_WORKER_COUNT = config.api_server.notification_worker.worker_count

    def __init__(self, router, storage, secret, external):
        self.router = router
        self.redis_pool: ConnectionsPool = storage['redis']['notification_queue']

    def route(self):
        self.router.add_route('GET', '', self.get_notifications)
        self.router.add_route('POST', '', self.create_notification)
        self.router.add_route('GET', '/{notification_uuid}', self.get_notification)
        self.router.add_route('POST', '/{notification_uuid}/:launch', self.launch_notification)

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
        notification_uuid = request.match_info['notification_uuid']
        notification = await find_notification_by_id(uuid=notification_uuid)

        if notification is None:
            return json_response(reason=f'notification not found {notification_uuid}', status=404)

        return json_response(result=notification_model_to_dict(notification))

    @request_error_handler
    async def create_notification(self, request):
        request: CreateNotificationRequest = convert_request(
            CreateNotificationRequest,
            await request.json(),
        )

        try:
            conditions = object_to_dict(
                deserialize.deserialize(ConditionClause, request.conditions)
            )
        except deserialize.exceptions.DeserializeException as error:
            return json_response(reason=f'wrong condition clause {error}', status=400)

        current_datetime = utc_now()
        if current_datetime >= request.scheduled_at:
            return json_response(reason=f'scheduled_at should later than current time', status=400)

        if request.scheduled_at is None:
            scheduled_at = current_datetime
        else:
            scheduled_at = request.scheduled_at

        notification = await create_notification(
            title=request.title,
            body=request.body,
            scheduled_at=scheduled_at,
            deep_link=request.deep_link,
            image_url=request.image_url,
            icon_url=request.icon_url,
            conditions=conditions,
        )
        return json_response(result=notification_model_to_dict(notification))

    @request_error_handler
    async def launch_notification(self, request):
        notification_uuid = request.match_info['notification_uuid']
        notification = await find_notification_by_id(uuid=notification_uuid)

        if notification is None:
            return json_response(reason=f'notification not found {notification_uuid}', status=404)

        notification = await change_notification_status(
            target_notification=notification,
            status=NotificationStatus.LAUNCHED,
        )

        conditions = deserialize.deserialize(ConditionClause, notification.conditions)
        device_total = await get_device_total_by_conditions(
            conditions=conditions
        )
        notification_job_capacity = math.ceil(device_total / self.NOTIFICATION_WORKER_COUNT)

        try:
            tasks = []
            with await self.redis_pool as redis_conn:
                for job_index in range(self.NOTIFICATION_WORKER_COUNT):
                    job: NotificationJob = deserialize.deserialize(
                        NotificationJob, {
                            'notification': {
                                'id': notification.id,
                                'uuid': str(notification.uuid),
                                'title': notification.title,
                                'body': notification.body,
                                'image_url': notification.image_url,
                                'icon_url': notification.icon_url,
                                'deep_link': notification.deep_link,
                                'conditions': object_to_dict(conditions),
                                'devices': {
                                    'start': job_index * notification_job_capacity,
                                    'size': notification_job_capacity,
                                }
                            },
                            'scheduled_at': notification.scheduled_at.isoformat()
                        }
                    )
                    tasks.append(
                        publish_notification_job(
                            redis_conn=redis_conn,
                            job=object_to_dict(job),
                            priority=0,
                        )
                    )
                await asyncio.gather(*tasks)
        except Exception as e:  # rollback if queue pushing failed
            logger.warning(f'rollback because of queue pushing failed {e}')
            notification = await change_notification_status(
                target_notification=notification,
                status=NotificationStatus.ERROR,
            )

        return json_response(result=notification_model_to_dict(notification))
