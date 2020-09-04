from typing import List, Optional

import deserialize

from common.structure.enum import DevicePlatform


@deserialize.default('extra', {})
class FCMJob:
    id: str
    push_tokens: List[str]
    device_platform: DevicePlatform
    title: str
    body: str
    image_url: Optional[str]
    deep_link: Optional[str]
    icon_url: Optional[str]
    extra: dict
