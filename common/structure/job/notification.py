from typing import List, Optional

import deserialize

from common.structure.condition import ConditionClause


@deserialize.default('notification', None)
@deserialize.default('device_ids', None)
@deserialize.default('conditions', None)
class NotificationJob:
    notification: Optional[str]
    device_ids: Optional[List[str]]
    conditions: Optional[List[ConditionClause]]
    scheduled_at: str  # iso 8601 format
