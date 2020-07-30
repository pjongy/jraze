from typing import List, Optional

import deserialize


@deserialize.default('extra', {})
class FCMJob:
    id: str
    push_tokens: List[str]
    title: str
    body: str
    image_url: Optional[str]
    deep_link: Optional[str]
    icon_url: Optional[str]
    extra: dict
