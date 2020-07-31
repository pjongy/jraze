from multiprocessing import Pool

from worker.push.fcm.config import config
from worker.push.fcm.replica import Replica

if __name__ == '__main__':
    size = int(config.push_worker.pool_size)
    with Pool(size) as pool:
        pool.map(
            Replica, [pid for pid in range(size)]
        )
