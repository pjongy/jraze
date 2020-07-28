from typing import Optional

import deserialize


@deserialize.default('id', None)
@deserialize.default('sent', 0)
@deserialize.default('failed', 0)
class ResultJob:
    id: Optional[str]
    sent: int
    failed: int
