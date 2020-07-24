import aiohttp_cors

import aioredis
from aiohttp import web

from apiserver.config import config
from apiserver.resource.devices import DevicesHttpResource
from apiserver.resource.notifications import NotificationsHttpResource
from common.logger.logger import get_logger
from common.storage.init import init_db


def plugin_app(app, prefix, nested, keys=()):
    for key in keys:
        nested[key] = app[key]
    app.add_subapp(prefix, nested)


async def application():
    logger = get_logger(__name__)

    app = web.Application(logger=logger)
    mysql_config = config.api_server.mysql
    await init_db(
        host=mysql_config.host,
        port=mysql_config.port,
        user=mysql_config.user,
        password=mysql_config.password,
        db=mysql_config.database,
    )

    redis_config = config.api_server.redis

    notification_queue_pool = await aioredis.create_pool(
        f'redis://{redis_config.host}:{redis_config.port}',
        password=redis_config.password,
        minsize=5,
        maxsize=10,
        db=int(redis_config.notification_queue.database),
    )

    storage = {
        'redis': {
            'notification_queue': notification_queue_pool,
        }
    }
    external = {}
    secret = {}
    resource_list = {
        '/devices': DevicesHttpResource,
        '/notifications': NotificationsHttpResource,
    }

    for path, resource in resource_list.items():
        subapp = web.Application(logger=logger)
        resource(
            router=subapp.router,
            storage=storage,
            secret=secret,
            external=external,
        ).route()
        plugin_app(app, path, subapp)

    cors = aiohttp_cors.setup(app)
    allow_url = '*'

    for route in list(app.router.routes()):
        cors.add(
            route,
            {
                allow_url: aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    allow_headers='*',
                    allow_methods=[route.method]
                )
            }
        )

    return app
