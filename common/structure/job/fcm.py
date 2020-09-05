import dataclasses
import enum
from typing import List, Optional

import deserialize

from common.structure.enum import DevicePlatform


@deserialize.default('extra', {})
@dataclasses.dataclass
class FCMSendPushMessageArgs:
    notification_id: str
    push_tokens: List[str]
    device_platform: DevicePlatform
    title: str
    body: str
    image_url: Optional[str]
    deep_link: Optional[str]
    icon_url: Optional[str]
    extra: dict


class FCMTask(enum.IntEnum):
    SEND_PUSH_MESSAGE = 1


@dataclasses.dataclass
class FCMJob:
    task: FCMTask
    kwargs: dict  # NOTE(pjongy): JSON data for task args e.g) FCMSendPushMessageArgs
