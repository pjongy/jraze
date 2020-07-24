from typing import List

import deserialize


@deserialize.default('image', '')
@deserialize.default('extra', {})
class Job:
    id: str
    registration_tokens: List[str]
    title: str
    body: str
    image: str
    extra: dict
