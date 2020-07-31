from typing import List

from common.model.device import Device
from common.model.device_notification_event import DeviceNotificationEvent, Event


async def add_device_notification_events(
    devices: List[Device],
    notification_id: int,
    event: Event
) -> None:
    return await DeviceNotificationEvent.bulk_create(
        [
            DeviceNotificationEvent(
                device=device,
                notification_id=notification_id,
                event=event
            )
            for device in devices
        ]
    )
