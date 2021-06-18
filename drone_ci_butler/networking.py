import redis
import socket
import logging
from elasticsearch import Elasticsearch
from drone_ci_butler.config import config


logger = logging.getLogger(__name__)


def get_elasticsearch_hostname():
    return resolve_hostname(config.elasticsearch_host)


def get_redis_hostname():
    return resolve_hostname(config.redis_host)


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


def get_redis_params() -> dict:
    return {
        "host": get_redis_hostname(),
        "port": config.redis_port,
        "db": config.redis_db,
    }


def get_elasticsearch_params():
    return {
        "host": get_elasticsearch_hostname(),
        "port": config.elasticsearch_port,
    }


def get_redis_pool() -> redis.ConnectionPool:
    params = get_redis_params()
    return redis.ConnectionPool(**params)


def connect_to_redis(pool=None) -> redis.Redis:
    if isinstance(pool, redis.ConnectionPool):
        logger.info(f"connecting to redis via pool {pool}")
        return redis.Redis(connection_pool=pool)

    params = get_redis_params()
    return redis.Redis(**params)
