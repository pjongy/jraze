import dataclasses
import datetime
from typing import List, Optional

import deserialize

from common.structure.condition import ConditionClause
from common.util import string_to_utc_datetime


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


@deserialize.parser('scheduled_at', string_to_utc_datetime)
@dataclasses.dataclass
class NotificationJob:
    notification: Optional[Notification]
    unrecorded: Optional[Unrecorded]
    scheduled_at: datetime.datetime
