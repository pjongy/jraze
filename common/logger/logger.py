import logging

from common.logger import logHandler


def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.addHandler(logHandler)
    return logger
