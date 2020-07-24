from apiserver.decorator.request import request_error_handler
from apiserver.resource import json_response, convert_request
from common.logger.logger import get_logger

logger = get_logger(__name__)


class CreateDeviceRequest:
    registration_id: str


class ModifyDeviceRequest:
    registration_id: str


class DevicesHttpResource:
    def __init__(self, router, storage, secret, external):
        self.router = router

    def route(self):
        self.router.add_route('POST', '', self.post)
        self.router.add_route('GET', '/{device_id}', self.get)
        self.router.add_route('PUT', '/{device_id}', self.put)

    @request_error_handler
    async def get(self, request):
        device_id = request.match_info['device_id']
        return json_response(result=device_id)

    @request_error_handler
    async def post(self, request):
        request = convert_request(CreateDeviceRequest, await request.json())
        return json_response(result=request)

    @request_error_handler
    async def put(self, request):
        request = convert_request(ModifyDeviceRequest, await request.json())
        return json_response(result=request)
