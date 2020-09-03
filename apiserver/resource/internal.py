from typing import List

from aiohttp.web_request import Request

from apiserver.exception.permission import ServerKeyError
from common.logger.logger import get_logger

logger = get_logger(__name__)


class InternalHttpResource:
    def __init__(self, router, storage, secret, external):
        self.router = router
        self.internal_api_keys: List[str] = secret['internal_api_keys']

    def _check_server_key(self, request: Request):
        x_server_key = request.headers.get('X-Server-Key')
        if x_server_key not in self.internal_api_keys:
            raise ServerKeyError()

    def route(self):
        pass
