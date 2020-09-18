from pathlib import Path

import deserialize

from common.configutil import get_config


class Config:
    @deserialize.parser('pool_size', int)
    class MessagingWorker:
        class APNs:
            class PEMCert:
                file_name: str

            class P8Cert:
                file_name: str
                key_id: str
                team_id: str
                topic: str  # Bundle id

            pem_cert: PEMCert
            p8_cert: P8Cert
            cert_type: str

        class FCM:
            class V1:
                project_id: str
                key_file_name: str

            class Legacy:
                server_key: str

            v1: V1
            legacy: Legacy
            client: str

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

        fcm: FCM
        apns: APNs
        pool_size: int
        redis: Redis

    push_worker: MessagingWorker


config_path = f'{Path(__file__).resolve().parent}/config'

config: Config = deserialize.deserialize(
    Config, get_config(config_path)
)