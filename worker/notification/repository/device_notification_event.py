from typing import List

from common.model.device import Device
from common.model.device_notification_event import DeviceNotificationEvent, Event
from common.model.notification import Notification


async def add_device_notification_events(
    devices: List[Device],
    notification: Notification,
    event: Event
) -> None:
    return await DeviceNotificationEvent.bulk_create(
        [
            DeviceNotificationEvent(
                device=device,
                notification=notification,
                event=event
            )
            for device in devices
        ]
    )
