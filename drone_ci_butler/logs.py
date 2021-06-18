import os
import logging
import colorlog
from cmreslogging.handlers import CMRESHandler


def get_elasticsearch_config():
    try:
        from drone_ci_butler.config import config
    except ImportError:
        config = None

    if not config:
        return

    return dict(host=config.elasticsearch_host, port=config.elasticsearch_port)


# fmt = "%(asctime)s %(log_color)s%(levelname)s%(reset)s %(name)s %(message)s"
fmt = "%(log_color)s%(levelname)s%(blue)s %(name)s %(reset)s%(message)s"
handler = logging.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(fmt))  # , "%Y-%m-%d %H:%M:%S"))

logger = logging.getLogger()

eshandler = CMRESHandler(
    hosts=[get_elasticsearch_config()],
    auth_type=CMRESHandler.AuthType.NO_AUTH,
    es_index_name="logs-drone-ci-butler",
)

logger.handlers = [handler, eshandler]


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
