import dataclasses
from typing import List, Optional

from common.structure.condition import ConditionClause


@dataclasses.dataclass
class Push:
    title: str
    body: str
    image_url: Optional[str]
    icon_url: Optional[str]
    deep_link: Optional[str]


@dataclasses.dataclass
class Notification(Push):
    @dataclasses.dataclass
    class Devices:
        start: int
        size: int
    id: int
    uuid: str
    conditions: Optional[ConditionClause]
    devices: Devices


@dataclasses.dataclass
class Unrecorded(Push):
    external_ids: Optional[List[str]]
    conditions: Optional[List[ConditionClause]]


@dataclasses.dataclass
class NotificationJob:
    notification: Optional[Notification]
    unrecorded: Optional[Unrecorded]
    scheduled_at: str
