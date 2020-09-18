from pathlib import Path
from typing import List

import deserialize

from common.configutil import get_config


class Config:
    @deserialize.default('internal_api_keys', [])
    @deserialize.parser('internal_api_keys', lambda arg: arg.split(','))
    @deserialize.default('port', 8080)
    @deserialize.parser('port', int)
    class APIServer:
        @deserialize.default('port', 3306)
        @deserialize.parser('port', int)
        class MySQL:
            host: str
            port: int
            user: str
            password: str
            database: str

        @deserialize.default('port', 27017)
        @deserialize.parser('port', int)
        class Mongo:
            host: str
            port: int
            user: str
            password: str
            database: str

        @deserialize.default('port', 6379)
        @deserialize.parser('port', int)
        class Redis:
            @deserialize.parser('database', int)
            class Database:
                database: int
            host: str
            port: int
            password: str

            notification_queue: Database

        @deserialize.parser('worker_count', int)
        class Worker:
            worker_count: int

        mysql: MySQL
        mongo: Mongo
        redis: Redis
        port: int
        notification_worker: Worker
        internal_api_keys: List[str]  # comma separated string to list

    api_server: APIServer


config_path = f'{Path(__file__).resolve().parent}/config'

config: Config = deserialize.deserialize(
    Config, get_config(config_path)
)
