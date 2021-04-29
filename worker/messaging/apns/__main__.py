from multiprocessing import Pool

from worker.messaging.apns.config import config
from worker.messaging.apns.replica import Replica

if __name__ == '__main__':
    size = int(config.push_worker.pool_size)
    with Pool(size) as pool:
        pool.map(
            Replica, [pid for pid in range(size)]
        )
