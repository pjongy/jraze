from pathlib import Path

import deserialize

from common.configutil import get_config


class Config:
    class NotificationWorker:
        @deserialize.default('port', 3306)
        @deserialize.parser('port', int)
        class MySQL:
            host: str
            port: int
            user: str
            password: str
            database: str

        class External:
            class Jraze:
                base_url: str
                x_server_key: str
            jraze: Jraze

        pool_size: str
        task_queue: MySQL
        external: External

    notification_worker: NotificationWorker


config_path = f'{Path(__file__).resolve().parent}/config'

config: Config = deserialize.deserialize(
    Config, get_config(config_path)
)
