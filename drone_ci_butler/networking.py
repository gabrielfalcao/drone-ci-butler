import redis
import socket
import logging
from urllib.parse import urlparse
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
        logger.error(f"could not resolve hostname {hostname}. Defaulting to {default}")
        return default


def resolve_zmq_address(address) -> str:
    default = address

    parsed = urlparse(address)
    items = parsed.netloc.split(":")
    port = None
    if len(items) == 2:
        hostname, port = items
    else:
        hostname = parsed.netloc

    if port:
        host = socket.gethostbyname(hostname)
    else:
        host = hostname

    netloc = host
    if port:
        netloc += f":{port}"

    return f"{parsed.scheme}://{netloc}"


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


def check_db_connection(engine):
    url = engine.url
    logger.info(f"Trying to connect to DB: {str(url)!r}")
    result = engine.connect()
    logger.info(f"SUCCESS: {url}")
    result.close()


def check_database_dns():
    try:
        logger.info(f"Check ability to resolve name: {config.database_hostname}")
        host = socket.gethostbyname(config.database_hostname)
        logger.info(f"SUCCESS: {config.database_hostname!r} => {host!r}")
    except Exception as e:
        return e

    if not config.database_port:
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        logger.info(f"Checking TCP connection to {host!r}")
        sock.connect((host, config.database_port))
        logger.info(f"SUCCESS: TCP connection to database works!!")
    except Exception as e:
        return e
    finally:
        sock.close()
