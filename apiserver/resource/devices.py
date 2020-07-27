import uuid
from typing import List

import deserialize

from apiserver.decorator.request import request_error_handler
from apiserver.repository.device import find_device_by_device_id, device_model_to_dict, \
    create_device, update_device, DevicePropertyBridge, add_device_properties, \
    device_property_model_to_dict, remove_device_properties
from apiserver.resource import json_response, convert_request
from common.logger.logger import get_logger
from common.model.device import DevicePlatform, SendPlatform

logger = get_logger(__name__)


@deserialize.default('device_platform', DevicePlatform.UNKNOWN)
@deserialize.default('send_platform', SendPlatform.UNKNOWN)
class CreateDeviceRequest:
    push_token: str
    send_platform: SendPlatform
    device_platform: DevicePlatform


@deserialize.default('device_platform', DevicePlatform.UNKNOWN)
@deserialize.default('send_platform', SendPlatform.UNKNOWN)
class UpdateDeviceRequest:
    push_token: str
    send_platform: SendPlatform
    device_platform: DevicePlatform


class UpdateDevicePropertiesRequest:
    properties: List[DevicePropertyBridge]


class DeleteDevicePropertiesRequest:
    properties: List[DevicePropertyBridge]


class DevicesHttpResource:
    def __init__(self, router, storage, secret, external):
        self.router = router

    def route(self):
        self.router.add_route('POST', '', self.create_device)
        self.router.add_route('GET', '/{device_id}', self.get_device)
        self.router.add_route('PUT', '/{device_id}', self.update_device)
        self.router.add_route('PATCH', '/{device_id}/properties', self.update_properties)
        self.router.add_route('DELETE', '/{device_id}/properties', self.delete_properties)

    @request_error_handler
    async def get_device(self, request):
        device_id = request.match_info['device_id']
        device = await find_device_by_device_id(device_id=device_id)

        if device is None:
            return json_response(reason=f'invalid device_id {device_id}', status=404)

        return json_response(result=device_model_to_dict(row=device))

    @request_error_handler
    async def create_device(self, request):
        request: CreateDeviceRequest = convert_request(CreateDeviceRequest, await request.json())

        device_id = str(uuid.uuid1())
        device = await create_device(
            device_id=device_id,
            push_token=request.push_token,
            send_platform=request.send_platform,
            device_platform=request.device_platform,
        )
        return json_response(result=device_model_to_dict(row=device))

    @request_error_handler
    async def update_device(self, request):
        device_id = request.match_info['device_id']
        request = convert_request(UpdateDeviceRequest, await request.json())
        target_device = await find_device_by_device_id(device_id=device_id)

        if target_device is None:
            return json_response(reason=f'invalid device_id {device_id}', status=404)

        device = await update_device(
            target_device=target_device,
            push_token=request.push_token,
            send_platform=request.send_platform,
            device_platform=request.device_platform,
        )
        return json_response(result=device_model_to_dict(row=device))

    @request_error_handler
    async def update_properties(self, request):
        device_id = request.match_info['device_id']
        request: UpdateDevicePropertiesRequest = convert_request(
            UpdateDevicePropertiesRequest,
            await request.json()
        )
        target_device = await find_device_by_device_id(device_id=device_id)

        if target_device is None:
            return json_response(reason=f'invalid device_id {device_id}', status=404)

        device_properties = await add_device_properties(
            target_device=target_device,
            device_properties=request.properties,
        )

        response = device_model_to_dict(row=target_device)
        response['device_properties'] += [
            device_property_model_to_dict(device_property)
            for device_property in device_properties
        ]

        return json_response(result=response)

    @request_error_handler
    async def delete_properties(self, request):
        device_id = request.match_info['device_id']
        request: DeleteDevicePropertiesRequest = convert_request(
            DeleteDevicePropertiesRequest,
            await request.json()
        )
        target_device = await find_device_by_device_id(device_id=device_id)

        if target_device is None:
            return json_response(reason=f'invalid device_id {device_id}', status=404)

        affected_rows = await remove_device_properties(
            target_device=target_device,
            device_properties=request.properties,
        )

        return json_response(result={'deleted': affected_rows})
