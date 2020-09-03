from typing import List, Optional

from common.structure.condition import ConditionClause


class Push:
    title: str
    body: str
    image_url: Optional[str]
    icon_url: Optional[str]
    deep_link: Optional[str]


class Notification(Push):
    class Devices:
        start: int
        size: int
    id: int
    uuid: str
    conditions: Optional[ConditionClause]
    devices: Devices


class Unrecorded(Push):
    external_ids: Optional[List[str]]
    conditions: Optional[List[ConditionClause]]


class NotificationJob:
    notification: Optional[Notification]
    unrecorded: Optional[Unrecorded]
    scheduled_at: str
