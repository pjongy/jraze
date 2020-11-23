from abc import ABC, abstractmethod
from logging import Logger

from aiohttp import web


class AbstractResource(ABC):
    def __init__(self, logger: Logger):
        self.app = web.Application(logger=logger)

    @abstractmethod
    def route(self):
        raise NotImplementedError('inherit class and implement method')
