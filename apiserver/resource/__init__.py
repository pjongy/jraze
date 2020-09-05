import json

import deserialize
from aiohttp import web

from apiserver.exception.request import IncompleteParameterError, TypeConvertError
from common.json_encoder import ManualJSONEncoder
from common.logger.logger import get_logger

logger = get_logger(__name__)


def json_response(
    result=None,
    reason=None,
    status=200,
    headers=None,
):
    if headers is None:
        headers = {}

    assert (result is None) ^ (
        reason is None), 'Either result or reason should be set'

    success = reason is None
    response = {
        'success': success,
        'result': result,
        'reason': reason,
    }

    return web.Response(
        body=json.dumps(response, cls=ManualJSONEncoder),
        content_type='application/json',
        status=status,
        headers=headers,
    )


def convert_request(class_, dict_):
    try:
        return deserialize.deserialize(
            class_, dict_
        )
    except TypeError as error:
        raise IncompleteParameterError(error)
    except deserialize.exceptions.DeserializeException as error:
        raise TypeConvertError(error)
