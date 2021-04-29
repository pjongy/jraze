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

        @deserialize.default('port', 3306)
        @deserialize.parser('port', int)
        class MySQL:
            host: str
            port: int
            user: str
            password: str
            database: str

        apns: APNs
        pool_size: int
        task_queue: MySQL

    push_worker: MessagingWorker


config_path = f'{Path(__file__).resolve().parent}/config'

config: Config = deserialize.deserialize(
    Config, get_config(config_path)
)
