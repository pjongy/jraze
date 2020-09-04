import dataclasses
from typing import List, Optional

import deserialize

from common.structure.enum import DevicePlatform


@deserialize.default('extra', {})
@dataclasses.dataclass
class APNsJob:
    id: str
    device_tokens: List[str]
    device_platform: DevicePlatform
    title: str
    body: str
    image_url: Optional[str]
    deep_link: Optional[str]
    icon_url: Optional[str]
    extra: dict
