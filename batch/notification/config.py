from pathlib import Path

import deserialize

from common.configutil import get_config


class Config:
    class NotificationBatchWorker:
        @deserialize.default('port', '6379')
        class Redis:
            @deserialize.parser('database', int)
            class Database:
                database: int

            host: str
            port: str
            password: str

            notification_queue: Database

        class External:
            class Jraze:
                base_url: str
                x_server_key: str
            jraze: Jraze

        @deserialize.parser('worker_count', int)
        class Worker:
            worker_count: int

        redis: Redis
        external: External
        work_term: int  # NOTE(pjongy): Work term in seconds
        notification_worker: Worker

    notification_batch: NotificationBatchWorker


config_path = f'{Path(__file__).resolve().parent}/config'

config: Config = deserialize.deserialize(
    Config, get_config(config_path)
)
