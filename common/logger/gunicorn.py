from gunicorn import glogging

from common.logger import formatter


class CustomLogger(glogging.Logger):
    def setup(self, cfg):
        super().setup(cfg)
        self._set_handler(self.error_log, cfg.errorlog, formatter)
        self._set_handler(self.access_log, cfg.accesslog, formatter)
