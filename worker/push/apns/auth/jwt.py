import jwt
import time


class AppleJWT:
    ALGORITHM = 'ES256'

    def __init__(self, key_file_name: str, key_id: str, team_id: str):
        self.key_id = key_id
        self.team_id = team_id

        p8_file = open(key_file_name)
        self.secret = p8_file.read()

    def generate(self):
        return jwt.encode(
            {
                'iss': self.team_id,
                'iat': time.time()
            },
            self.secret,
            algorithm=self.ALGORITHM,
            headers={
                'alg': self.ALGORITHM,
                'kid': self.key_id,
            }
        )
