import socket

from elasticsearch import Elasticsearch
from drone_ci_butler.config import config
from drone_ci_butler.logs import get_logger

logger = get_logger(__name__)


def get_elasticsearch_hostname():
    return resolve_hostname(config.elasticsearch_host)


def resolve_hostname(hostname, default="localhost") -> str:
    try:
        return socket.gethostbyname(hostname)
    except Exception:
        logger.warning(
            f"could not resolve hostname {hostname}. Defaulting to {default}"
        )
        return default


def connect_to_elasticsearch() -> Elasticsearch:
    hosts = [get_elasticsearch_hostname()]
    return Elasticsearch(hosts, maxsize=config.elasticsearch_pool_size)
