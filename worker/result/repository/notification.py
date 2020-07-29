from tortoise.expressions import F

from common.model.notification import Notification, NotificationStatus
from common.util import utc_now


async def increase_sent_count(
    _id: str,
    sent: int = None,
) -> int:
    return await Notification.filter(
        id=_id
    ).update(
        sent=F('sent') + sent
    )


async def change_notification_status(
    _id: str,
    status: NotificationStatus
) -> int:
    return await Notification.filter(
        id=_id
    ).update(
        status=status,
        modified_at=utc_now(),
    )
