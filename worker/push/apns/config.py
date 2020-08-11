from pathlib import Path

import deserialize

from common.configutil import get_config


class Config:
    @deserialize.parser('pool_size', int)
    class APNsPushWorker:
        class APNs:
            key_file_name: str
            key_id: str
            team_id: str

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

        apns: APNs
        pool_size: int
        redis: Redis

    push_worker: APNsPushWorker


config_path = f'{Path(__file__).resolve().parent}/config'

config: Config = deserialize.deserialize(
    Config, get_config(config_path)
)
