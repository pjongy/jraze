from common.model.notification import Notification


async def find_notification_by_id(uuid: str) -> Notification:
    return await Notification.filter(
        uuid=uuid
    ).first()
