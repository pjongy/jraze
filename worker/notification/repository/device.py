from typing import List

from tortoise.query_utils import Q

from common.model.device import Device
from common.structure.condition import ConditionClause


def _resolve_condition_clause_to_q(condition_clause: ConditionClause):
    if condition_clause.conditions is not None:
        repeatable_clause = []
        for _condition_clause in condition_clause.conditions:
            repeatable_clause.append(_resolve_condition_clause_to_q(_condition_clause))
        return Q(*repeatable_clause, join_type=condition_clause.join_type)
    parameter = {
        'device_properties__key': condition_clause.key,
        'device_properties__value': condition_clause.value
    }
    return Q(**parameter)


async def find_devices_by_conditions(
    conditions: ConditionClause,
    start: int = 0,
    size: int = 10,
    order_bys: List[str] = (),
) -> List[Device]:
    filter_ = _resolve_condition_clause_to_q(conditions)
    query_set = Device.filter(filter_)
    for order_by in order_bys:
        if order_by.isascii():
            query_set = query_set.order_by(order_by)
    return await query_set.offset(start).limit(size).all()
