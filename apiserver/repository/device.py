from typing import List

from tortoise import QuerySet

from apiserver.model.device import Device


def device_model_to_dict(row: Device):
    device_dict = {
        'id': row.id,
        'external_id': row.external_id,
    }
    return device_dict


def _device_relational_query_set(query_set: QuerySet[Device]) -> QuerySet[Device]:
    return query_set


async def find_device_by_external_id(external_id: str) -> Device:
    return await _device_relational_query_set(
        Device.filter(
            external_id=external_id
        ).order_by(
            'modified_at', 'created_at'
        )
    ).first()


async def find_devices_by_external_ids(external_ids: List[str]) -> List[Device]:
    query = _device_relational_query_set(
        Device.filter(
            external_id__in=external_ids
        ).order_by(
            'modified_at', 'created_at'
        )
    )
    return await query.all()


async def create_device(
    external_id: str,
) -> Device:
    return await Device.create(
        external_id=external_id,
    )
