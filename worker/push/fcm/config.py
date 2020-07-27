from pathlib import Path

import deserialize

from common.configutil import get_config


class Config:
    class FCMPushWorker:
        class Firebase:
            server_key: str

        @deserialize.default('port', '6379')
        class Redis:
            class Database:
                database: str

            host: str
            port: str
            password: str

            notification_queue: Database

        firebase: Firebase
        pool_size: str
        redis: Redis

    push_worker: FCMPushWorker


config_path = f'{Path(__file__).resolve().parent}/config'

config: Config = deserialize.deserialize(
    Config, get_config(config_path)
)
