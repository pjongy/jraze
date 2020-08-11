from typing import List, Optional

import deserialize


@deserialize.default('extra', {})
class APNsJob:
    id: str
    device_tokens: List[str]
    title: str
    body: str
    image_url: Optional[str]
    deep_link: Optional[str]
    icon_url: Optional[str]
    extra: dict
