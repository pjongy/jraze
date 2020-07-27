from typing import List

import deserialize


@deserialize.default('image', '')
@deserialize.default('extra', {})
class FCMJob:
    id: str
    push_tokens: List[str]
    title: str
    body: str
    image: str
    extra: dict
