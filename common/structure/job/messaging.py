import dataclasses
import enum
from typing import List, Optional

import deserialize

from common.structure.enum import DevicePlatform, SendPlatform


@deserialize.default('extra', {})
@dataclasses.dataclass
class SendPushMessageArgs:
    send_platform: SendPlatform
    device_platform: DevicePlatform
    notification_id: str
    push_tokens: List[str]
    title: str
    body: str
    image_url: Optional[str]
    deep_link: Optional[str]
    icon_url: Optional[str]
    extra: dict


class MessagingTask(enum.IntEnum):
    SEND_PUSH_MESSAGE = 1


@dataclasses.dataclass
class MessagingJob:
    task: MessagingTask
    kwargs: dict  # NOTE(pjongy): JSON data for task args e.g) FCMSendPushMessageArgs
