import datetime
from typing import List

from common.model.notification import Notification, NotificationStatus
from common.util import utc_now


def notification_model_to_dict(row: Notification):
    notification_dict = {
        'id': row.id,
        'title': row.title,
        'body': row.body,
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
    status: NotificationStatus,
    start: int,
    size: int,
    order_bys: List[str] = ()
) -> List[Notification]:
    query_set = Notification.filter(
        status=status
    )
    for order_by in order_bys:
        if order_by.isascii():
            query_set = query_set.order_by(order_by)
    return await query_set.offset(start).limit(size).all()


async def find_notification_by_id(_id: str) -> Notification:
    return await Notification.filter(
        id=_id
    ).first()


async def create_notification(
    title: str,
    body: str,
    deep_link: str = None,
    image_url: str = None,
    icon_url: str = None,
    conditions=None,
    scheduled_at: datetime.datetime = None,
) -> Notification:
    if conditions is None:
        conditions = {}

    return await Notification.create(
        title=title,
        body=body,
        deep_link=deep_link,
        image_url=image_url,
        icon_url=icon_url,
        conditions=conditions,
        scheduled_at=scheduled_at,
        status=NotificationStatus.CREATED,
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
