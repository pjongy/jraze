from tortoise.expressions import F

from common.model.notification import Notification, NotificationStatus
from common.util import utc_now


async def increase_sent_count(
    uuid: str,
    sent: int = None,
) -> int:
    return await Notification.filter(
        uuid=uuid
    ).update(
        sent=F('sent') + sent
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
