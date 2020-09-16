from abc import ABC, abstractmethod
from typing import Tuple, List


class AbstractFCM(ABC):
    @abstractmethod
    async def send_data(
        self,
        targets: List[str],
        data: dict
    ) -> Tuple[int, int]:
        raise NotImplementedError('inherit class and implement method')
