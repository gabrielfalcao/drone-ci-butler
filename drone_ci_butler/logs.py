import os
import logging
import colorlog

# fmt = "%(asctime)s %(log_color)s%(levelname)s%(reset)s %(name)s %(message)s"
fmt = "%(log_color)s%(levelname)s%(blue)s %(name)s %(reset)s%(message)s"
handler = logging.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(fmt))  # , "%Y-%m-%d %H:%M:%S"))

logger = logging.getLogger()

logger.handlers = [handler]


def reset_level(envvar_fallback="INFO"):
    target_level = str(
        os.environ.get("DRONE_CI_BUTLER_LOGLEVEL", envvar_fallback)
    ).upper()

    if target_level in dir(logging):
        level = getattr(logging, target_level)
    else:
        level = logging.INFO

    logger.setLevel(level)


def get_logger(name=None):
    return logging.getLogger(name)


reset_level()
logger = get_logger("drone_ci_butler")
