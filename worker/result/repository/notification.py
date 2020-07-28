from tortoise.expressions import F

from common.model.notification import Notification, NotificationStatus


async def increase_sent_count(
    _id: str,
    sent: int = None,
) -> int:
    return await Notification.filter(
        id=_id
    ).update(
        sent=F('sent') + sent
    )
