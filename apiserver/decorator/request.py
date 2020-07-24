import functools
import json

from aiohttp import web

from apiserver.exception.request import RequestError
from common.logger.logger import get_logger

logger = get_logger(__name__)


def request_error_handler(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except json.decoder.JSONDecodeError as e:
            error_msg = 'Not JSON type'
            status = 400
            logger.error(e)
        except PermissionError as e:
            error_msg = 'Permission error'
            status = 403
            logger.error(e)
        except RequestError as e:
            error_msg = str(e)
            status = 400
            logger.error(e)

        return web.Response(
            body=json.dumps({
                'success': False,
                'result': '',
                'reason': error_msg,
            }),
            content_type='application/json',
            status=status,
        )

    return wrapper
