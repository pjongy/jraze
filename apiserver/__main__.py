import sys
import asyncio

from aiohttp import web

from apiserver.application import application
from apiserver.config import config
from common.logger.logger import get_logger

if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)


async def main():
    logger = get_logger(__name__)
    runner = web.AppRunner(await application())
    await runner.setup()
    port = config.api_server.port
    site = web.TCPSite(runner, port=port, backlog=1024)
    await site.start()
    logger.debug(f'Run server / {port}')

    # Infinite loop for maintaining server alive
    # https://github.com/aio-libs/aiohttp/blob/master/aiohttp/web.py#L365
    while True:
        await asyncio.sleep(100 * 3600)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_forever()
