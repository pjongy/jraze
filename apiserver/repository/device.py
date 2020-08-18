from typing import List, Tuple

import tortoise
from tortoise import QuerySet
from tortoise.query_utils import Q

from common.model.device import Device, SendPlatform, DevicePlatform
from common.model.device_property import DeviceProperty
from common.structure.condition import ConditionClause
from common.util import utc_now


def device_model_to_dict(row: Device):
    device_dict = {
        'id': row.id,
        'device_id': row.device_id,
        'push_token': row.push_token,
        'send_platform': row.send_platform,
        'device_platform': row.device_platform,
        'created_at': row.created_at,
        'modified_at': row.modified_at,
    }
    try:
        device_dict['device_properties'] = [
            device_property_model_to_dict(row=device_property)
            for device_property in row.device_properties
        ]
    except tortoise.exceptions.NoValuesFetched:
        device_dict['device_properties'] = []

    return device_dict


def device_property_model_to_dict(row: DeviceProperty):
    return {
        row.key: row.value,
    }


def _device_relational_query_set(query_set: QuerySet[Device]) -> QuerySet[Device]:
    return query_set.prefetch_related(
        'device_properties'
    )


async def find_device_by_device_id(device_id: str) -> Device:
    return await _device_relational_query_set(
        Device.filter(
            device_id=device_id
        ).order_by(
            'modified_at', 'created_at'
        )
    ).first()


async def find_device_by_push_token(
    push_token: str,
    send_platform: SendPlatform
) -> Device:
    return await _device_relational_query_set(
        Device.filter(
            push_token=push_token, send_platform=send_platform
        ).order_by(
            'modified_at', 'created_at'
        )
    ).first()


async def create_device(
    device_id: str,
    push_token: str = None,
    send_platform: SendPlatform = SendPlatform.UNKNOWN,
    device_platform: DevicePlatform = DevicePlatform.UNKNOWN,
) -> Device:
    return await Device.create(
        device_id=device_id,
        send_platform=send_platform,
        push_token=push_token,
        device_platform=device_platform,
    )


async def update_device(
    target_device: Device,
    push_token: str = None,
    send_platform: SendPlatform = SendPlatform.UNKNOWN,
    device_platform: DevicePlatform = DevicePlatform.UNKNOWN,
) -> Device:
    target_device.send_platform = send_platform
    target_device.push_token = push_token
    target_device.device_platform = device_platform
    target_device.modified_at = utc_now()
    await target_device.save()
    return target_device


class DevicePropertyBridge:
    key: str
    value: str


async def add_device_properties(
    target_device: Device,
    device_properties: List[DevicePropertyBridge] = (),
) -> List[DeviceProperty]:
    addition_items = []
    for device_property in device_properties:
        addition_items.append(
            DeviceProperty(
                device=target_device,
                key=device_property.key,
                value=device_property.value,
            )
        )
    if addition_items:
        await DeviceProperty.bulk_create(addition_items)

    return addition_items


async def remove_device_properties(
    target_device: Device,
    device_properties: List[DevicePropertyBridge] = (),
) -> int:
    conditions = [
        Q(
            device=target_device,
            key=device_property.key,
            value=device_property.value,
        )
        for device_property in device_properties
    ]

    return await DeviceProperty.filter(
        Q(*conditions, join_type='OR')
    ).delete()


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


async def get_device_total_by_conditions(
    conditions: ConditionClause,
) -> int:
    filter_ = _resolve_condition_clause_to_q(conditions)
    query_set = Device.filter(filter_)
    return await query_set.count()


async def find_devices_by_conditions(
    conditions: ConditionClause,
    start: int = 0,
    size: int = 10,
    order_bys: List[str] = (),
) -> List[Device]:
    filter_ = _resolve_condition_clause_to_q(conditions)
    query_set = _device_relational_query_set(Device.filter(filter_))
    for order_by in order_bys:
        if order_by.isascii():
            query_set = query_set.order_by(order_by)
    return await query_set.offset(start).limit(size).all()


async def search_devices(
    device_ids: List[str],
    conditions: ConditionClause,
    start: int = 0,
    size: int = 10,
    order_bys: List[str] = (),
) -> Tuple[int, List[Device]]:
    filter_ = Q()
    if conditions.key is not None:
        filter_ = _resolve_condition_clause_to_q(conditions)
    device_id_filter = Q()
    if device_ids:
        device_id_filter = Q(device_id__in=device_ids)
    query_set = _device_relational_query_set(
        Device.filter(filter_, device_id_filter)
    )
    for order_by in order_bys:
        if order_by.isascii():
            query_set = query_set.order_by(order_by)
    return (
        await query_set.count(),
        await query_set.offset(start).limit(size).all()
    )
