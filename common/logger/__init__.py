import logging

from pythonjsonlogger import jsonlogger

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logging.basicConfig(
    level='INFO',
    handlers=[logHandler]
)
