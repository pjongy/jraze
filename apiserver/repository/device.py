from typing import List

import tortoise
from tortoise import QuerySet
from tortoise.query_utils import Q

from common.model.device import Device, SendPlatform, DevicePlatform
from common.model.device_property import DeviceProperty
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
