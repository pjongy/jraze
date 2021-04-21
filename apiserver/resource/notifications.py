import dataclasses
import datetime
from typing import List, Optional

import deserialize
from jasyncq.dispatcher.model.task import TaskIn
from jasyncq.dispatcher.tasks import TasksDispatcher

from apiserver.decorator.request import request_error_handler
from apiserver.dispatcher.device import DeviceDispatcher
from apiserver.repository.notification import find_notifications_by_status, \
    notification_model_to_dict, find_notification_by_id, create_notification, \
    change_notification_status
from apiserver.resource import json_response, convert_request
from apiserver.resource.abstract import AbstractResource
from common.logger.logger import get_logger
from apiserver.model.notification import NotificationStatus
from common.structure.condition import ConditionClause
from common.structure.job.notification import NotificationTask
from common.util import string_to_utc_datetime, utc_now

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


class UpdateNotificationStatusRequest:
    status: NotificationStatus


class NotificationsHttpResource(AbstractResource):
    def __init__(
        self,
        device_dispatcher: DeviceDispatcher,
        notification_task_queue: TasksDispatcher,
    ):
        super().__init__(logger=logger)
        self.router = self.app.router
        self.device_dispatcher = device_dispatcher
        self.notification_task_queue = notification_task_queue

    def route(self):
        self.router.add_route('GET', '', self.get_notifications)
        self.router.add_route('POST', '', self.create_notification)
        self.router.add_route('GET', '/{notification_uuid}', self.get_notification)
        self.router.add_route('POST', '/{notification_uuid}/:launch', self.launch_notification)
        self.router.add_route('PUT', '/{notification_uuid}/status', self.update_notification_status)

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
            conditions = dataclasses.asdict(
                deserialize.deserialize(ConditionClause, request.conditions)
            )
        except deserialize.exceptions.DeserializeException as error:
            return json_response(reason=f'wrong condition clause {error}', status=400)

        current_datetime = utc_now()

        if request.scheduled_at is None:
            scheduled_at = current_datetime
        else:
            scheduled_at = request.scheduled_at

        if current_datetime > scheduled_at:
            return json_response(reason=f'scheduled_at should later than current time', status=400)

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
    async def update_notification_status(self, request):
        notification_uuid = request.match_info['notification_uuid']
        notification = await find_notification_by_id(uuid=notification_uuid)

        if notification is None:
            return json_response(reason=f'notification not found {notification_uuid}', status=404)

        request_body: UpdateNotificationStatusRequest = convert_request(
            UpdateNotificationStatusRequest,
            await request.json(),
        )
        notification = await change_notification_status(
            target_notification=notification,
            status=request_body.status,
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
            status=NotificationStatus.QUEUED,
        )
        conditions = deserialize.deserialize(ConditionClause, notification.conditions)

        tasks = [{
            'task': NotificationTask.LAUNCH_NOTIFICATION,
            'kwargs': {
                'notification': {
                    'id': notification.id,
                    'uuid': str(notification.uuid),
                    'title': notification.title,
                    'body': notification.body,
                    'image_url': notification.image_url,
                    'icon_url': notification.icon_url,
                    'deep_link': notification.deep_link,
                },
                'conditions': dataclasses.asdict(conditions),
            },
        }]
        try:
            await self.notification_task_queue.apply_tasks(
                tasks=[
                    TaskIn(
                        task=task,
                        queue_name='NOTIFICATION_JOB_QUEUE',
                        scheduled_at=int(notification.scheduled_at.timestamp()),
                    )
                    for task in tasks
                ],
            )
        except Exception as e:  # rollback if queue pushing failed
            logger.warning(f'rollback because of queue pushing failed {e}')
            notification = await change_notification_status(
                target_notification=notification,
                status=NotificationStatus.ERROR,
            )

        return json_response(result=notification_model_to_dict(notification))
