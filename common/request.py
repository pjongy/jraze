import json
import urllib.parse

import aiohttp

from common.logger.logger import get_logger

logger = get_logger(__name__)


async def _json_response(response):
    json_ = None
    try:
        json_ = await response.json()
    except json.decoder.JSONDecodeError:
        logger.exception('Unknown filter element (JSONDecodeError)')
    except aiohttp.ContentTypeError:
        logger.exception(f'Empty response {response.status}')

    return response.status, json_, response.headers


class Request:
    DEFAULT_HEADERS = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    DEFAULT_HEADERS_FORM_DATA = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    async def post(self, url='', parameters=None, headers=None, is_json=True):
        if headers is None:
            headers = {}
        if parameters is None:
            parameters = {}

        logger.debug(f'POST request to {url}')
        if is_json:
            post_params = {'json': parameters}
            default_header = self.DEFAULT_HEADERS
        else:
            post_params = {'data': parameters}
            default_header = self.DEFAULT_HEADERS_FORM_DATA
        async with aiohttp.ClientSession(headers={**default_header, **headers}) as session:
            async with session.post(url, **post_params) as resp:
                return await _json_response(resp)

    async def delete(self, url='', parameters=None, headers=None):
        if headers is None:
            headers = self.DEFAULT_HEADERS
        if parameters is None:
            parameters = {}

        req_url = f'{url}?{urllib.parse.urlencode(parameters)}'
        logger.debug(f'DELETE request to {req_url}')
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.delete(req_url) as resp:
                return await _json_response(resp)

    async def put(self, url='', parameters=None, headers=None, is_json=True):
        if headers is None:
            headers = {}
        if parameters is None:
            parameters = {}

        logger.debug(f'PUT request to {url}')
        if is_json:
            post_params = {'json': parameters}
            default_header = self.DEFAULT_HEADERS
        else:
            post_params = {'data': parameters}
            default_header = self.DEFAULT_HEADERS_FORM_DATA
        async with aiohttp.ClientSession(headers={**default_header, **headers}) as session:
            async with session.put(url, **post_params) as resp:
                return await _json_response(resp)

    async def get(self, url='', parameters=None, headers=None):
        if headers is None:
            headers = self.DEFAULT_HEADERS
        if parameters is None:
            parameters = {}

        logger.debug(f'GET request to {url}')
        req_url = f'{url}?{urllib.parse.urlencode(parameters)}'
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(req_url) as resp:
                return await _json_response(resp)
