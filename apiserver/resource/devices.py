from typing import List, Any

import deserialize

from apiserver.decorator.request import request_error_handler
from apiserver.repository.device import find_device_by_external_id, device_model_to_dict, \
    create_device, update_device, DevicePropertyBridge, add_device_properties, \
    device_property_model_to_dict, remove_device_properties, search_devices
from apiserver.repository.device_notification_log import find_notification_events_by_external_id, \
    device_notification_log_model_to_dict
from apiserver.resource import json_response, convert_request
from common.logger.logger import get_logger
from apiserver.model.device import DevicePlatform, SendPlatform
from common.structure.condition import ConditionClause

logger = get_logger(__name__)


@deserialize.default('device_platform', DevicePlatform.UNKNOWN)
@deserialize.default('send_platform', SendPlatform.UNKNOWN)
class UpdateDeviceRequest:
    external_id: str
    push_token: str
    send_platform: SendPlatform
    device_platform: DevicePlatform


class DevicePropertyObject:
    key: str
    value: Any


class AddDevicePropertiesRequest:
    properties: List[DevicePropertyObject]


class DeleteDevicePropertiesRequest:
    properties: List[DevicePropertyObject]


@deserialize.default('start', 0)
@deserialize.default('size', 10)
@deserialize.default('order_bys', [])
@deserialize.parser('order_bys', lambda arg: arg.split(','))  # comma separated string to list
@deserialize.parser('start', int)
@deserialize.parser('size', int)
class FetchDeviceNotificationEventsRequest:
    start: int
    size: int
    order_bys: List[str]


@deserialize.parser('start', int)
@deserialize.parser('size', int)
@deserialize.default('external_ids', [])
@deserialize.default('conditions', {})
@deserialize.default('order_bys', [])
class SearchDevicesRequest:
    external_ids: List[str]
    conditions: dict
    start: int
    size: int
    order_bys: List[str]


class DevicesHttpResource:
    def __init__(self, router, storage, secret, external):
        self.router = router

    def route(self):
        self.router.add_route('PUT', '', self.upsert_device)
        self.router.add_route('GET', '/{external_id}', self.get_device)
        self.router.add_route('DELETE', '/{external_id}/properties', self.delete_properties)
        self.router.add_route(
            'GET',
            '/{external_id}/notifications',
            self.get_notification_events
        )
        self.router.add_route('POST', '/-/:search', self.search_devices)
        self.router.add_route('POST', '/{external_id}/properties/:add', self.add_properties)

    @request_error_handler
    async def get_device(self, request):
        external_id = request.match_info['external_id']
        device = await find_device_by_external_id(external_id=external_id)

        if device is None:
            return json_response(reason=f'invalid external_id {external_id}', status=404)

        return json_response(result=device_model_to_dict(row=device))

    @request_error_handler
    async def search_devices(self, request):
        request: SearchDevicesRequest = convert_request(SearchDevicesRequest, await request.json())

        try:
            conditions: ConditionClause = deserialize.deserialize(
                ConditionClause, request.conditions)
        except deserialize.exceptions.DeserializeException as error:
            return json_response(reason=f'wrong condition clause {error}', status=400)

        total, devices = await search_devices(
            external_ids=request.external_ids,
            conditions=conditions,
            start=request.start,
            size=request.size,
            order_bys=request.order_bys,
        )

        return json_response(result={
            'total': total,
            'devices': [
                device_model_to_dict(device)
                for device in devices
            ]
        })

    @request_error_handler
    async def upsert_device(self, request):
        request: UpdateDeviceRequest = convert_request(
            UpdateDeviceRequest, await request.json())
        external_id = request.external_id
        target_device = await find_device_by_external_id(external_id=external_id)

        if target_device is None:
            device = await create_device(
                external_id=external_id,
                push_token=request.push_token,
                send_platform=request.send_platform,
                device_platform=request.device_platform,
            )
        else:
            device = await update_device(
                target_device=target_device,
                push_token=request.push_token,
                send_platform=request.send_platform,
                device_platform=request.device_platform,
            )
        return json_response(result=device_model_to_dict(row=device))

    def _convert_property(self, properties: List[DevicePropertyObject]):
        device_property_bridges = []
        for property_ in properties:
            if type(property_.value) is str:
                device_property_bridges.append(
                    DevicePropertyBridge(
                        key=property_.key,
                        value_str=property_.value,
                        value_int=None
                    )
                )
            elif type(property_.value) is int:
                device_property_bridges.append(
                    DevicePropertyBridge(
                        key=property_.key,
                        value_str=None,
                        value_int=property_.value
                    )
                )
            else:
                raise TypeError('int/str type only (properties.value)')
        return device_property_bridges

    @request_error_handler
    async def add_properties(self, request):
        external_id = request.match_info['external_id']
        request: AddDevicePropertiesRequest = convert_request(
            AddDevicePropertiesRequest,
            await request.json()
        )
        target_device = await find_device_by_external_id(external_id=external_id)

        if target_device is None:
            return json_response(reason=f'invalid external_id {external_id}', status=404)

        try:
            properties = self._convert_property(request.properties)
        except TypeError as e:
            return json_response(reason=e.args[0], status=400)

        device_properties = await add_device_properties(
            target_device=target_device,
            device_properties=properties,
        )

        response = device_model_to_dict(row=target_device)
        response['device_properties'] += [
            device_property_model_to_dict(device_property)
            for device_property in device_properties
        ]

        return json_response(result=response)

    @request_error_handler
    async def delete_properties(self, request):
        external_id = request.match_info['external_id']
        request: DeleteDevicePropertiesRequest = convert_request(
            DeleteDevicePropertiesRequest,
            await request.json()
        )
        target_device = await find_device_by_external_id(external_id=external_id)

        if target_device is None:
            return json_response(reason=f'invalid external_id {external_id}', status=404)

        try:
            properties = self._convert_property(request.properties)
        except TypeError as e:
            return json_response(reason=e.args[0], status=400)

        affected_rows = await remove_device_properties(
            target_device=target_device,
            device_properties=properties,
        )

        return json_response(result={'deleted': affected_rows})

    @request_error_handler
    async def get_notification_events(self, request):
        external_id = request.match_info['external_id']
        query_params: FetchDeviceNotificationEventsRequest = convert_request(
            FetchDeviceNotificationEventsRequest,
            dict(request.rel_url.query),
        )
        available_order_by_fields = {
            'created_at', '-created_at',
            'id', '-id',
        }

        device = await find_device_by_external_id(external_id=external_id)

        if device is None:
            return json_response(reason=f'invalid external_id {external_id}', status=404)

        total, events = await find_notification_events_by_external_id(
            device=device,
            start=query_params.start,
            size=query_params.size,
            order_bys=list(available_order_by_fields.intersection(query_params.order_bys)),
        )

        return json_response(result={
            'total': total,
            'events': [
                device_notification_log_model_to_dict(event)
                for event in events
            ]
        })
