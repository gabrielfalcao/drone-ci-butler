import logging
import colorlog

# fmt = "%(asctime)s %(log_color)s%(levelname)s%(reset)s %(name)s %(message)s"
fmt = "%(log_color)s%(levelname)s%(blue)s %(name)s %(reset)s%(message)s"
handler = logging.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(fmt))  # , "%Y-%m-%d %H:%M:%S"))

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.handlers = [handler]


def get_logger(name=None):
    return logging.getLogger(name)


logger = get_logger("drone_ci_butler")
