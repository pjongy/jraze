from typing import List

from tortoise.query_utils import Q

from apiserver.repository.notification import notification_model_to_dict
from common.model.device import Device
from common.model.device_notification_event import Event, DeviceNotificationEvent


def device_notification_event_model_to_dict(row: DeviceNotificationEvent):
    device_notification_event_dict = {
        'id': row.id,
        'notification': notification_model_to_dict(row.notification),
        'event': row.event,
        'created_at': row.created_at,
    }
    return device_notification_event_dict


async def find_notification_events_by_device_id(
    device: Device,
    start: int = 0,
    size: int = 10,
    events: List[Event] = (),
    order_bys: List[str] = (),
):
    event_filter = [
        Q(device=device)
    ]
    if events:
        event_filter.append(Q(event__in=events))

    query_set = DeviceNotificationEvent.filter(Q(*event_filter)).prefetch_related(
        'device', 'notification'
    )
    for order_by in order_bys:
        if order_by.isascii():
            query_set = query_set.order_by(order_by)
    return (
        await query_set.count(),
        await query_set.offset(start).limit(size).all()
    )
