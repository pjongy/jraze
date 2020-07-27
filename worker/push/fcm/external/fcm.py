from typing import List, Tuple

from common.request import Request


class FCM(Request):
    FCM_API_HOST = 'https://fcm.googleapis.com'

    def __init__(self, server_key):
        self.server_key = server_key

    async def send_notification(
        self,
        targets: List[str],
        body: str,
        title: str,
        image: str = None
    ) -> Tuple[int, int]:
        PUSH_SEND_PATH = '/fcm/send'
        body = {
            "notification": {
                "body": body,
                "title": title,
            },
            "registration_ids": targets
        }
        if image is not None:
            body['notification']['image'] = image
        status, response, _ = await self.post(
            url=f'{self.FCM_API_HOST}{PUSH_SEND_PATH}',
            parameters=body,
            headers={'Authorization': f'key={self.server_key}'}
        )

        if not 200 <= status < 300:
            raise PermissionError(f'fcm notification sent failed {response}')

        return response['success'], response['failure']

    async def send_data(
        self,
        targets: List[str],
        data: dict
    ) -> Tuple[int, int]:
        PUSH_SEND_PATH = '/fcm/send'
        body = {
            "data": data,
            "registration_ids": targets
        }
        status, response, _ = await self.post(
            url=f'{self.FCM_API_HOST}{PUSH_SEND_PATH}',
            parameters=body,
            headers={'Authorization': f'key={self.server_key}'}
        )

        if not 200 <= status < 300:
            raise PermissionError(f'fcm data sent failed {response}')

        return response['success'], response['failure']
