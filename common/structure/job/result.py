import dataclasses
from typing import Optional

import deserialize

from common.structure.enum import DevicePlatform


@deserialize.default('id', None)
@deserialize.default('sent', 0)
@deserialize.default('failed', 0)
@dataclasses.dataclass
class ResultJob:
    id: Optional[str]
    sent: int
    device_platform: DevicePlatform
    failed: int
