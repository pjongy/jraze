from common.model.notification import Notification


async def find_notification_by_id(_id: str) -> Notification:
    return await Notification.filter(
        id=_id
    ).first()
