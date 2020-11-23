import aiohttp_cors
import aiomysql

import motor.motor_asyncio
from aiohttp import web
from jasyncq.dispatcher.tasks import TasksDispatcher
from jasyncq.repository.tasks import TaskRepository

from apiserver.config import config
from apiserver.dispatcher.device import DeviceDispatcher
from apiserver.resource.abstract import AbstractResource
from apiserver.resource.devices import DevicesHttpResource
from apiserver.resource.internal import InternalHttpResource
from apiserver.resource.notifications import NotificationsHttpResource
from common.logger.logger import get_logger
from apiserver.storage.init import init_db


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

    mongo_config = config.api_server.mongo
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
        f'mongodb://{mongo_config.user}:{mongo_config.password}'
        f'@{mongo_config.host}:{mongo_config.port}'
    )[mongo_config.database]

    task_queue_config = config.api_server.task_queue
    task_queue_pool = await aiomysql.create_pool(
        host=task_queue_config.host,
        port=task_queue_config.port,
        user=task_queue_config.user,
        password=task_queue_config.password,
        db=task_queue_config.database,
        autocommit=False,
    )

    notification_task_queue_repository = TaskRepository(
        pool=task_queue_pool,
        topic_name='NOTIFICATION_TOPIC',
    )
    await notification_task_queue_repository.initialize()
    notification_task_queue = TasksDispatcher(
        repository=notification_task_queue_repository,
    )

    resource_list = {
        '/devices': DevicesHttpResource(
            device_dispatcher=DeviceDispatcher(
                database=mongo_client
            )
        ),
        '/notifications': NotificationsHttpResource(
            device_dispatcher=DeviceDispatcher(
                database=mongo_client
            ),
            notification_task_queue=notification_task_queue,
        ),
        '/internal': InternalHttpResource(
            internal_api_keys=config.api_server.internal_api_keys,
        ),
    }

    for path, resource in resource_list.items():
        resource: AbstractResource = resource  # NOTE(pjongy): For type hinting
        resource.route()
        plugin_app(app, path, resource.app)

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
