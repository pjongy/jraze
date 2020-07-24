from apiserver.decorator.request import request_error_handler
from apiserver.resource import json_response
from common.logger.logger import get_logger

logger = get_logger(__name__)


class NotificationsHttpResource:
    def __init__(self, router, storage, secret, external):
        self.router = router

    def route(self):
        self.router.add_route('GET', '', self.get)

    @request_error_handler
    async def get(self, request):
        return json_response(result='test')
