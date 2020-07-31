from multiprocessing import Pool

from worker.result.config import config
from worker.result.replica import Replica

if __name__ == '__main__':
    size = int(config.result_worker.pool_size)
    with Pool(size) as pool:
        pool.map(
            Replica, [pid for pid in range(size)]
        )
