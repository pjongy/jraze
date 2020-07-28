from pathlib import Path

import deserialize

from common.configutil import get_config


class Config:
    class ResultWorker:
        @deserialize.default('port', '6379')
        class Redis:
            class Database:
                database: str

            host: str
            port: str
            password: str

            notification_queue: Database

        pool_size: str
        redis: Redis

    result_worker: ResultWorker


config_path = f'{Path(__file__).resolve().parent}/config'

config: Config = deserialize.deserialize(
    Config, get_config(config_path)
)
