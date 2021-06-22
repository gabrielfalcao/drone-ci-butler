import socket

from elasticsearch import Elasticsearch
from drone_ci_butler.config import config
from drone_ci_butler.logs import get_logger
from drone_ci_butler.networking import resolve_hostname

logger = get_logger(__name__)


def get_elasticsearch_hostname():
    result = resolve_hostname(config.elasticsearch_host)
    logger.debug(f"resolved elasticsearch host {config.elasticsearch_host}: {result}")
    return result


def connect_to_elasticsearch() -> Elasticsearch:
    hosts = [get_elasticsearch_hostname()]
    logger.info(f"using elasticsearch hosts {hosts}")
    return Elasticsearch(hosts, maxsize=config.elasticsearch_pool_size)
