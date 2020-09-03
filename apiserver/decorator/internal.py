import functools
import json

from aiohttp import web

from apiserver.exception.permission import ServerKeyError


def restrict_external_request_handler(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ServerKeyError as e:
            error_msg = e.message

        return web.Response(
            body=json.dumps({
                'success': False,
                'result': '',
                'reason': error_msg,
            }),
            content_type='application/json',
            status=403,
        )
    return wrapper
