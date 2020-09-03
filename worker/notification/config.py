from pathlib import Path

import deserialize

from common.configutil import get_config


class Config:
    class NotificationWorker:
        @deserialize.default('port', '6379')
        class Redis:
            class Database:
                database: str

            host: str
            port: str
            password: str

            notification_queue: Database

        class External:
            class Jraze:
                base_url: str
                x_server_key: str
            jraze: Jraze

        pool_size: str
        redis: Redis
        external: External

    notification_worker: NotificationWorker


config_path = f'{Path(__file__).resolve().parent}/config'

config: Config = deserialize.deserialize(
    Config, get_config(config_path)
)
