import datetime
import uuid
from typing import List, Tuple

from tortoise.expressions import F
from tortoise.query_utils import Q

from common.model.notification import Notification, NotificationStatus
from common.util import utc_now


def notification_model_to_dict(row: Notification):
    notification_dict = {
        'id': row.id,
        'uuid': row.uuid,
        'title': row.title,
        'body': row.body,
        'sent': {
            'android': row.sent_android,
            'ios': row.sent_ios,
        },
        'deep_link': row.deep_link,
        'image_url': row.image_url,
        'icon_url': row.icon_url,
        'conditions': row.conditions,
        'status': row.status,
        'scheduled_at': row.scheduled_at,
        'created_at': row.created_at,
        'modified_at': row.modified_at,
    }
    return notification_dict


async def find_notifications_by_status(
    status: NotificationStatus = None,
    start: int = 0,
    size: int = 10,
    order_bys: List[str] = ()
) -> Tuple[int, List[Notification]]:
    notification_filter = Q()
    if status is not None:
        notification_filter = Q(status=status)

    query_set = Notification.filter(notification_filter)
    for order_by in order_bys:
        if order_by.isascii():
            query_set = query_set.order_by(order_by)
    return (
        await query_set.count(),
        await query_set.offset(start).limit(size).all()
    )


async def find_notification_by_id(uuid: str) -> Notification:
    return await Notification.filter(
        uuid=uuid
    ).first()


async def create_notification(
    title: str,
    body: str,
    scheduled_at: datetime.datetime,
    deep_link: str = None,
    image_url: str = None,
    icon_url: str = None,
    conditions=None,
) -> Notification:
    if conditions is None:
        conditions = {}

    return await Notification.create(
        uuid=uuid.uuid1(),
        title=title,
        body=body,
        deep_link=deep_link,
        image_url=image_url,
        icon_url=icon_url,
        conditions=conditions,
        scheduled_at=scheduled_at,
        status=NotificationStatus.DRAFT,
    )


async def update_notification(
    target_notification: Notification,
    **kwargs
) -> Notification:
    available_fields = ['title', 'body', 'icon_url', 'image_url', 'deep_link', 'scheduled_at']
    for k, v in kwargs.items():
        if k in available_fields and v is not None:
            setattr(target_notification, k, v)
    target_notification.modified_at = utc_now()
    await target_notification.save()
    return target_notification


async def change_notification_status(
    target_notification: Notification,
    status: NotificationStatus
) -> Notification:
    target_notification.status = status
    target_notification.modified_at = utc_now()
    await target_notification.save()
    return target_notification


async def increase_sent_count(
    uuid_: str,
    sent_ios: int = 0,
    sent_android: int = 0,
) -> int:
    return await Notification.filter(
        uuid=uuid_
    ).update(
        sent_ios=F('sent_ios') + sent_ios,
        sent_android=F('sent_android') + sent_android,
    )
