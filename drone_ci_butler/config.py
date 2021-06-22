import os
import yaml
import json
import redis
import logging
import multiprocessing
from sqlalchemy.engine.url import make_url
from typing import Optional, List, Any, Dict
from functools import lru_cache
from pathlib import Path
from collections import defaultdict
from uiclasses import DataBag, DataBagChild, UserFriendlyObject
from drone_ci_butler.exceptions import ConfigMissing, UserFriendlyException
from drone_ci_butler.meta import MetaConfig, ConfigProperty
from drone_ci_butler.util import load_yaml


logger = logging.getLogger(__name__)


class Config(DataBag, metaclass=MetaConfig):
    def __init__(
        self,
        path=None,
        path_location_env_var="DRONE_CI_BUTLER_CONFIG_PATH",
        default_path="~/.drone-ci-butler.yml",
    ):
        self.path = (
            Path(path or os.getenv(path_location_env_var) or default_path)
            .expanduser()
            .absolute()
        )
        self.__data__ = {}
        self.__data__.update(self.resolve_values(self.path))

    def to_env_vars(self) -> Dict[str, str]:
        env = {}
        for field in self.__fields__.values():
            if field.env:
                env[field.env] = self.resolve_property(field, data=dict(self))
        return env

    def to_shell_env_declaration(self) -> str:
        parts = [
            f"{key}={value}"
            for key, value in sorted(self.to_env_vars().items(), key=lambda kv: kv[0])
        ]
        return "\n".join(parts)

    def to_docker_env_declaration(self) -> str:
        parts = [
            f"ENV {key} {value}"
            for key, value in sorted(self.to_env_vars().items(), key=lambda kv: kv[0])
        ]
        return "\n".join(parts)

    def resolve_property(
        self,
        field: ConfigProperty,
        name: Optional[str] = None,
        data: DataBag = None,
        fail: bool = False,
    ) -> Any:
        name = name or field.name
        container = DataBag(data or {})
        try:
            value = field.resolve(container, file_path=self.path)
        except Exception as e:
            if fail:
                raise
            value = field.default_value

        if field.env:
            container[field.env] = value

        if name:
            container[name] = value

        # resolve nested value
        for attr in field.path[:-1]:
            if not container.get(attr):
                container[attr] = {}

        last = field.path[-1]
        container[last] = value
        return value

    def resolve_values(self, path: Path) -> Dict[str, Any]:
        data = load_yaml(path)
        for name, field in self.__fields__.items():
            value = self.resolve_property(field, name, data=data)
            setattr(self, name, value)
        return data

    REDIS_HOST = ConfigProperty(
        "redis",
        "host",
        env="REDIS_HOST",
        default_value="localhost",
    )
    SESSION_FILE_DIR = ConfigProperty(
        "session",
        "file_dir",
        env="SESSION_FILE_DIR",
        default_value="/tmp/",
    )

    REDIS_PORT = ConfigProperty(
        "redis",
        "port",
        env="REDIS_PORT",
        default_value=6379,
        deserialize=int,
    )
    REDIS_DB = ConfigProperty(
        "redis",
        "db",
        env="REDIS_DB",
        default_value=0,
        deserialize=int,
    )
    SECRET_KEY = ConfigProperty(
        "auth",
        "flask_secret",
        env="SECRET_KEY",
    )
    GITHUB_CLIENT_ID = ConfigProperty(
        "github", "app", "client_id", env="DRONE_GITHUB_CLIENT_ID"
    )

    GITHUB_CLIENT_SECRET = ConfigProperty(
        "github", "app", "client_secret", env="DRONE_GITHUB_CLIENT_SECRET"
    )

    SLACK_CLIENT_SECRET = ConfigProperty(
        "slack", "oauth", "client_secret", env="SLACK_CLIENT_SECRET"
    )

    SLACK_CLIENT_ID = ConfigProperty(
        "slack", "oauth", "client_id", env="SLACK_CLIENT_ID"
    )

    SLACK_SIGNING_SECRET = ConfigProperty(
        "slack", "oauth", "signing_secret", env="SLACK_SIGNING_SECRET"
    )

    SLACK_VERIFICATION_TOKEN = ConfigProperty(
        "slack",
        "oauth",
        "verification_token",
        env="SLACK_VERIFICATION_TOKEN",
    )
    SLACK_BOT_TOKEN = ConfigProperty(
        "slack",
        "oauth",
        "bot_token",
        env="SLACK_BOT_TOKEN",
    )

    SLACK_APP_USER_TOKEN = ConfigProperty(
        "slack",
        "oauth",
        "app_user_token",
        env="SLACK_APP_USER_TOKEN",
    )
    slack_state_path = ConfigProperty(
        "slack",
        "store",
        "state_path",
        env="SLACK_STORE_STATE_PATH",
        default_value=".slack/state",
    )
    slack_installation_path = ConfigProperty(
        "slack",
        "store",
        "installation_path",
        env="SLACK_STORE_INSTALLATION_PATH",
        default_value=".slack/installation",
    )

    database_hostname = ConfigProperty(
        "postgres",
        "host",
        default_value="postgres",
        env="POSTGRES_HOST",
    )
    database_name = ConfigProperty(
        "postgres",
        "db",
        default_value="drone_ci_butler",
        env="POSTGRES_DB",
    )
    database_user = ConfigProperty(
        "postgres",
        "user",
        default_value="drone_ci_butler",
        env="POSTGRES_USER",
    )
    database_password = ConfigProperty(
        "postgres",
        "password",
        default_value="drone_ci_butler",
        env="POSTGRES_PASSWORD",
    )
    database_port = ConfigProperty(
        "postgres",
        "port",
        env="POSTGRES_PORT",
        default_value=5432,
        deserialize=int,
    )
    database_auth_method = ConfigProperty(
        "postgres",
        "host_auth_method",
        default_value="trust",
        env="POSTGRES_HOST_AUTH_METHOD",
    )
    drone_url = ConfigProperty(
        "drone",
        "server",
        env="DRONE_SERVER_URL",
    )
    drone_access_token = ConfigProperty(
        "drone",
        "access_token",
        env="DRONE_ACCESS_TOKEN",
    )

    drone_github_owner = ConfigProperty(
        "drone",
        "api",
        "owner",
        env="DRONE_GITHUB_OWNER",
    )
    drone_github_repo = ConfigProperty(
        "drone",
        "api",
        "repo",
        env="DRONE_GITHUB_REPO",
    )
    auth_jwt_secret = ConfigProperty(
        "auth",
        "jwt_secret",
        env="DRONE_CI_BUTLER_JWT_SECRET",
    )

    worker_queue_rep_address = ConfigProperty(
        "workers",
        "queue_rep_address",
        env="DRONE_CI_BUTLER_QUEUE_REP_ADDRESS",
        default_value="tcp://127.0.0.1:5555",
    )

    worker_queue_pull_address = ConfigProperty(
        "workers",
        "queue_pull_address",
        env="DRONE_CI_BUTLER_QUEUE_PULL_ADDRESS",
        default_value="tcp://127.0.0.1:5556",
    )

    worker_push_address = ConfigProperty(
        "workers",
        "push_address",
        env="DRONE_CI_BUTLER_PUSH_ADDRESS",
        default_value="tcp://127.0.0.1:6666",
    )

    worker_pull_address = ConfigProperty(
        "workers",
        "pull_address",
        env="DRONE_CI_BUTLER_PULL_ADDRESS",
        default_value="tcp://127.0.0.1:7777",
    )

    worker_monitor_address = ConfigProperty(
        "workers",
        "monitor_address",
        env="DRONE_CI_BUTLER_MONITOR_ADDRESS",
        default_value="tcp://127.0.0.1:5001",
    )

    worker_control_address = ConfigProperty(
        "workers",
        "control_address",
        env="DRONE_CI_BUTLER_CONTROL_ADDRESS",
        default_value="tcp://127.0.0.1:5002",
    )

    web_host = ConfigProperty(
        "web",
        "hostname",
        env="DRONE_CI_BUTLER_WEB_HOSTNAME",
        default_value="0.0.0.0",
    )
    web_port = ConfigProperty(
        "web",
        "port",
        env="DRONE_CI_BUTLER_WEB_PORT",
        default_value=4000,
    )

    max_workers_per_process = ConfigProperty(
        "workers",
        "max_per_process",
        env="DRONE_CI_BUTLER_MAX_GREENLETS_PER_PROCESS",
        default_value=multiprocessing.cpu_count(),
        deserialize=int,
    )
    drone_api_owner = ConfigProperty(
        "drone",
        "api",
        "owner",
        env="DRONE_API_OWNER",
        deserialize=str,
    )
    drone_api_repo = ConfigProperty(
        "drone",
        "api",
        "repo",
        env="DRONE_API_REPO",
        deserialize=str,
    )

    drone_api_max_pages = ConfigProperty(
        "drone",
        "api",
        "max_pages",
        env="DRONE_API_MAX_PAGES",
        default_value=100000,
        deserialize=int,
    )
    drone_api_initial_page = ConfigProperty(
        "drone",
        "api",
        "initial_page",
        env="DRONE_API_INITIAL_PAGE",
        default_value=0,
        deserialize=int,
    )
    drone_api_max_builds = ConfigProperty(
        "drone",
        "api",
        "max_builds",
        env="DRONE_API_MAX_BUILDS",
        default_value=250000,
        deserialize=int,
    )
    elasticsearch_host = ConfigProperty(
        "elasticsearch",
        "hostname",
        env="DRONE_CI_BUTLER_ELASTICSEARCH_HOSTNAME",
        default_value="localhost",
    )
    elasticsearch_port = ConfigProperty(
        "elasticsearch",
        "port",
        env="DRONE_CI_BUTLER_ELASTICSEARCH_PORT",
        default_value=9200,
        deserialize=int,
    )
    elasticsearch_pool_size = ConfigProperty(
        "elasticsearch",
        "pool_size",
        env="DRONE_CI_BUTLER_ELASTICSEARCH_POOL_SIZE",
        default_value=multiprocessing.cpu_count(),
        deserialize=int,
    )

    elastic_search_logs_index = ConfigProperty(
        "elasticsearch",
        "logs_index",
        env="DRONE_CI_BUTLER_ELASTICSEARCH_LOGS_INDEX",
        default_value="drone_ci_butler_logs",
    )

    logging_level_default = ConfigProperty(
        "logging",
        "default_level",
        env="DRONE_CI_BUTLER_DEFAULT_LOGLEVEL",
        default_value="DEBUG",
        deserialize=lambda x: str(x).upper(),
    )
    enable_json_logging = ConfigProperty(
        "logging",
        "enable_json",
        env="DRONE_CI_BUTLER_ENABLE_JSON_LOGGING",
        deserialize=bool,
    )

    @property
    def sqlalchemy_uri(self) -> str:
        return f"postgresql://{self.database_user}:{self.database_password}@{self.database_hostname}:{self.database_port}/{self.database_name}"

    @property
    @lru_cache()
    def SESSION_REDIS(self):
        if self.REDIS_HOST and self.REDIS_PORT:
            return redis.Redis(
                host=self.REDIS_HOST,
                port=self.REDIS_PORT,
                db=self.REDIS_DB,
            )

    @property
    def SESSION_TYPE(self) -> str:
        if self.REDIS_HOST and self.REDIS_PORT:
            return "redis"
        else:
            return "filesystem"

    @property
    def GITHUB_AUTHORIZE_PARAMS(self) -> dict:
        return {}  # {"scope": "repo user read:user user:email"}

    @property
    def slack_installation_store_path(self) -> Path:
        p = Path(self.slack_installation_path).expanduser().absolute()
        p.mkdir(exist_ok=True, parents=True)
        return p

    @property
    def slack_state_store_path(self) -> Path:
        p = Path(self.slack_state_path).expanduser().absolute()
        p.mkdir(exist_ok=True, parents=True)
        return p

    @property
    def logging_mapping(self) -> Dict[str, str]:

        try:
            mapping = dict(self.traverse("logging", "mapping") or {})
        except Exception as e:
            raise UserFriendlyException(
                f"Invalid logging mapping, not a dict: {repr(mapping)}"
            )

        if not isinstance(mapping, dict):
            raise RuntimeError(f"Invalid logging mapping, not a dict: {repr(mapping)}")
            return {}

        return mapping


config = Config()
