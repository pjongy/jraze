import dataclasses
import enum
from random import randint
from typing import Dict, Union, List

import deserialize
import pymongo
from motor.core import AgnosticDatabase, AgnosticCollection
from motor.motor_asyncio import AsyncIOMotorCursor
from pymongo import ReturnDocument

from common.logger.logger import get_logger
from common.structure.condition import ConditionClause


class DevicePlatform(enum.IntEnum):
    UNKNOWN = 0
    ANDROID = 1
    IOS = 2
    WEB = 3


class SendPlatform(enum.IntEnum):
    UNKNOWN = 0
    FCM = 1
    APNS = 2


DevicePropertyValue = Union[
    str, int, float, List[Union[str, int, float]]
]


@deserialize.default('device_properties', {})
@deserialize.parser('_id', str)
@dataclasses.dataclass
class Device:
    _id: str
    id: int  # NOTE(pjongy): MySQL PK field for backward-compatibility
    random_bucket: int
    external_id: str
    push_token: str
    send_platform: SendPlatform
    device_platform: DevicePlatform
    device_properties: Dict[str, DevicePropertyValue]


def _resolve_condition_clause_to_filter(
    condition_clause: ConditionClause
):
    available_join_types = {
        'OR': '$or',
        'AND': '$and',
    }
    operators = {
        'int_eq': ('$eq', int),
        'int_gt': ('$gt', int),
        'int_gte': ('$gte', int),
        'int_lt': ('$lt', int),
        'int_lte': ('$lte', int),
        'str_exists': ('$elemMatch', str),
        'str_eq': ('$eq', str),
    }

    if condition_clause.conditions is not None:
        if condition_clause.join_type not in available_join_types:
            raise ValueError('Unknown join_type in ConditionClause')
        repeatable_clause = []
        for _condition_clause in condition_clause.conditions:
            repeatable_clause.append(_resolve_condition_clause_to_filter(_condition_clause))
        return {
            available_join_types[condition_clause.join_type]: repeatable_clause
        }
    if condition_clause.operator not in operators:
        raise ValueError('Unknown operator in ConditionClause')

    op = operators[condition_clause.operator]
    return {
        f'device_properties.{condition_clause.key}': {
            op[0]: op[1](condition_clause.value)
        }
    }


logger = get_logger(__name__)


class DeviceDispatcher:
    COLLECTION_NAME = 'device'

    def __init__(self, database: AgnosticDatabase):
        self.database = database
        self.collection: AgnosticCollection = self.database[self.COLLECTION_NAME]

    async def upsert_device_by_external_id(
        self,
        rdb_pk: int,
        external_id: str,
        push_token: str,
        send_platform: SendPlatform,
        device_platform: DevicePlatform,
    ) -> Device:
        filter_ = {'external_id': external_id}
        document = {
            'id': rdb_pk,
            'external_id': external_id,
            'push_token': push_token,
            'send_platform': send_platform,
            'device_platform': device_platform,
            'random_bucket': randint(1, 10000),
        }
        update = {
            '$set': document
        }

        result: dict = await self.collection.find_one_and_update(
            filter=filter_,
            update=update,
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        logger.debug(result)

        return deserialize.deserialize(Device, result)

    async def upsert_property_by_external_id(
        self,
        external_id: str,
        property_key: str,
        property_value: DevicePropertyValue = None
    ) -> Device:
        filter_ = {'external_id': external_id}

        if property_value is None:  # NOTE(pjongy): Remove attribute
            update = {
                '$unset': {
                    f'device_properties.{property_key}': '',
                }
            }
        else:
            update = {
                '$set': {
                    f'device_properties.{property_key}': property_value,
                }
            }

        result: dict = await self.collection.find_one_and_update(
            filter=filter_,
            update=update,
            return_document=ReturnDocument.AFTER,
        )
        logger.debug(result)

        return deserialize.deserialize(Device, result)

    async def get_device_total_by_condition(
        self,
        external_ids: List[str],
        condition_clause: ConditionClause,
    ) -> int:
        condition_filter = _resolve_condition_clause_to_filter(condition_clause=condition_clause)
        external_id_filter = {}
        if external_ids:
            external_id_filter = {
                'external_id': {
                    '$in': external_ids
                }
            }
        filter_ = {
            '$and': [condition_filter, external_id_filter]
        }
        total: int = await self.collection.count_documents(
            filter=filter_,
        )
        logger.debug(total)
        return total

    async def search_devices(
        self,
        external_ids: List[str],
        condition_clause: ConditionClause,
        start: int = 0,
        size: int = 10,
        order_bys: List[str] = (),
    ) -> List[Device]:
        condition_filter = _resolve_condition_clause_to_filter(condition_clause=condition_clause)
        external_id_filter = {}
        if external_ids:
            external_id_filter = {
                'external_id': {
                    '$in': external_ids
                }
            }

        filter_ = {
            '$and': [condition_filter, external_id_filter]
        }

        sort = []
        for order_by in order_bys:
            if order_by.startswith('-'):
                direction = pymongo.ASCENDING
                key = order_by[1:]
            else:
                direction = pymongo.DESCENDING
                key = order_by
            sort.append((key, direction))

        result: AsyncIOMotorCursor = self.collection.find(
            filter=filter_,
            skip=start,
            limit=size,
            sort=sort,
        )
        logger.debug(result)

        return [
            deserialize.deserialize(Device, device)
            async for device in result
        ]

    async def find_device_by_external_id(self, external_id: str):
        filter_ = {
            'external_id': external_id,
        }
        result: dict = await self.collection.find_one(
            filter=filter_,
        )
        logger.debug(result)

        return deserialize.deserialize(Device, result)
