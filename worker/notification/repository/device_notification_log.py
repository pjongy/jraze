from typing import List

from common.model.device import Device
from common.model.device_notification_log import DeviceNotificationLog


async def add_device_notification_logs(
    devices: List[Device],
    notification_id: int,
) -> None:
    return await DeviceNotificationLog.bulk_create(
        [
            DeviceNotificationLog(
                device=device,
                notification_id=notification_id,
            )
            for device in devices
        ]
    )
