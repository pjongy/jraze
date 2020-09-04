from tortoise.expressions import F

from common.model.notification import Notification, NotificationStatus
from common.util import utc_now


async def increase_sent_count(
    uuid: str,
    sent_ios: int = 0,
    sent_android: int = 0,
) -> int:
    return await Notification.filter(
        uuid=uuid
    ).update(
        sent_ios=F('sent_ios') + sent_ios,
        sent_android=F('sent_android') + sent_android,
    )


async def change_notification_status(
    uuid: str,
    status: NotificationStatus
) -> int:
    return await Notification.filter(
        uuid=uuid
    ).update(
        status=status,
        modified_at=utc_now(),
    )
