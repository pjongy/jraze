from typing import List

from tortoise.query_utils import Q

from apiserver.repository.notification import notification_model_to_dict
from common.model.device import Device
from common.model.device_notification_log import DeviceNotificationLog


def device_notification_log_model_to_dict(row: DeviceNotificationLog):
    device_notification_log_dict = {
        'id': row.id,
        'notification': notification_model_to_dict(row.notification),
        'created_at': row.created_at,
    }
    return device_notification_log_dict


async def find_notification_events_by_external_id(
    device: Device,
    start: int = 0,
    size: int = 10,
    order_bys: List[str] = (),
):
    filter_ = [
        Q(device=device)
    ]

    query_set = DeviceNotificationLog.filter(Q(*filter_)).prefetch_related(
        'device', 'notification'
    )
    for order_by in order_bys:
        if order_by.isascii():
            query_set = query_set.order_by(order_by)
    return (
        await query_set.count(),
        await query_set.offset(start).limit(size).all()
    )
