from multiprocessing import Pool

from worker.notification.config import config
from worker.notification.replica import Replica

if __name__ == '__main__':
    size = int(config.notification_worker.pool_size)
    with Pool(size) as pool:
        replica = Replica()
        pool.map(
            replica.run, [pid for pid in range(size)]
        )
