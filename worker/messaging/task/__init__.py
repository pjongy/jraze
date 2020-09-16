from abc import ABC, abstractmethod


class AbstractTask(ABC):
    @abstractmethod
    async def run(
        self,
        kwargs: dict
    ):
        raise NotImplementedError('inherit class and implement method')
