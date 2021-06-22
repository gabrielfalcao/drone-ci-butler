import sys
import os
import logging
import warnings
import colorlog

from cmreslogging.handlers import CMRESHandler
from elasticsearch.exceptions import ElasticsearchWarning
from pythonjsonlogger import jsonlogger
from drone_ci_butler.config import config
from drone_ci_butler.networking import get_elasticsearch_params

CHATTY_LOGGER_NAMES = ["parso", "asyncio", "filelock"]

# fmt = "%(asctime)s %(log_color)s%(levelname)s%(reset)s %(name)s %(message)s"
fmt = "%(log_color)s%(levelname)s%(blue)s %(name)s %(reset)s%(message)s"
handler = logging.StreamHandler()

if config.enable_json_logging or not sys.stdout.isatty():
    handler.setFormatter(jsonlogger.JsonFormatter())

else:
    handler.setFormatter(colorlog.ColoredFormatter(fmt))  # , "%Y-%m-%d %H:%M:%S"))


logger = logging.getLogger()

eshandler = None
if config.elasticsearch_host:
    warnings.simplefilter("ignore", category=ElasticsearchWarning)
    eshandler = CMRESHandler(
        hosts=[get_elasticsearch_params()],
        auth_type=CMRESHandler.AuthType.NO_AUTH,
        es_index_name=config.elastic_search_logs_index,
    )
    eshandler.setFormatter(jsonlogger.JsonFormatter())


def get_default_level():
    return getattr(logging, config.logging_level_default, logging.DEBUG)


def silence_chatty_loggers(next_level=logging.WARNING):
    for name in CHATTY_LOGGER_NAMES:
        get_logger(name).setLevel(next_level)


def reset_level(target_level=config.logging_level_default):
    if target_level in dir(logging):
        level = getattr(logging, target_level)
    else:
        level = get_default_level()

    if eshandler:
        logger.handlers = [handler, eshandler]
    else:
        logger.handlers = [handler]

    logger.setLevel(level)
    silence_chatty_loggers()
    apply_mapping()


def apply_mapping():
    try:
        for logger_name, level_name in config.logging_mapping.items():
            logging.getLogger(logger_name).setLevel(
                getattr(logging, level_name, get_default_level())
            )
    except Exception as e:
        logger.exception(f"failed to map log levels to logger names: {e}")


def get_logger(name=None):
    return logging.getLogger(name)


get_logger("elasticsearch").setLevel(logging.WARNING)

reset_level()
logger = get_logger("drone_ci_butler")
