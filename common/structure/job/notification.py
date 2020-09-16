import dataclasses
import enum
from typing import Optional

from common.structure.condition import ConditionClause
from common.structure.enum import DevicePlatform


@dataclasses.dataclass
class Range:
    start: int
    size: int


@dataclasses.dataclass
class Notification:
    id: int
    uuid: str
    title: str
    body: str
    image_url: Optional[str]
    icon_url: Optional[str]
    deep_link: Optional[str]


@dataclasses.dataclass
class NotificationLaunchMessageArgs:
    notification: Notification
    conditions: Optional[ConditionClause]
    device_range: Range


@dataclasses.dataclass
class NotificationSentResultMessageArgs:
    device_platform: DevicePlatform
    notification_uuid: str
    sent: int
    failed: int


class NotificationTask(enum.IntEnum):
    LAUNCH_NOTIFICATION = 1
    UPDATE_RESULT = 2


@dataclasses.dataclass
class NotificationJob:
    task: NotificationTask
    kwargs: dict  # NOTE(pjongy): JSON data for task args e.g) NotificationLaunchMessageArgs
