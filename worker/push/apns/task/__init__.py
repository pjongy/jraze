from abc import ABC, abstractmethod
from typing import Optional

from common.structure.job.result import ResultJob


class AbstractTask(ABC):
    @abstractmethod
    async def run(
        self,
        kwargs: dict
    ) -> Optional[ResultJob]:
        raise NotImplementedError('inherit class and implement method')
