import logging
import colorlog


def get_logger(name=None, level=logging.INFO, fmt='%(log_color)s%(levelname)s:%(name)s:%(message)s'):
    logger = colorlog.getLogger(name)
    logger.setLevel(level)
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(fmt))
    logger.addHandler(handler)
    return logger


get_logger()
logger = get_logger('drone_ci_butler')
