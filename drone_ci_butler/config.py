import os
import yaml
import json
import redis
from typing import Optional, List, Any, Dict
from functools import lru_cache
from pathlib import Path
from collections import defaultdict
from uiclasses import DataBag, DataBagChild, UserFriendlyObject
from drone_ci_butler.logs import get_logger
from drone_ci_butler.exceptions import ConfigMissing

logger = get_logger(__name__)


def load_yaml(path: Path) -> dict:
    try:
        path = path.expanduser().absolute()
        with path.open() as fd:
            return yaml.load(fd, Loader=yaml.FullLoader)
    except Exception as e:
        logger.warning(f"failed to load path {path}: {e}")
        return {}


class ConfigProperty(UserFriendlyObject):
    name: str
    path: List[str]
    fallback_env: str
    default_value: Any

    def __init__(self, *path: List[str], **kw):
        name = kw.pop("name", None)
        fallback_env = kw.pop("fallback_env", None)
        default_value = kw.pop("default_value", None)

        if not path and not fallback_env:
            raise SyntaxError(
                f"ConfigProperty requires at least one path name, or a fallback_env keyword-arg"
            )
        for k, v in dict(
            name=name or fallback_env,
            path=list(path),
            fallback_env=fallback_env,
            default_value=default_value,
            **kw,
        ).items():
            setattr(self, k, v)

    def resolve(self, config: DataBag, file_path: Optional[Path]):
        name = self.name or self.fallback_env
        attr = ".".join(self.path)
        value = None
        if self.path:
            value = config.traverse(*self.path)

        if not value and self.fallback_env:
            value = os.getenv(self.fallback_env)

        if not value and self.default_value is not None:
            value = self.default_value

        if value is None:
            raise ConfigMissing(
                attr,
                file_path,
                self.fallback_env,
            )

        return value


class MetaConfig(type):
    def __new__(cls, name, bases, attributes):
        config_properties = dict(
            [(k, v) for k, v in attributes.items() if isinstance(v, ConfigProperty)]
        )
        attributes["__fields__"] = config_properties
        return type.__new__(cls, name, bases, attributes)
        return cls


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
            if field.fallback_env:
                env[field.fallback_env] = self.resolve_property(field, data=dict(self))
        return env

    def to_env_declaration(self) -> str:
        parts = [
            f"{key}={value}"
            for key, value in sorted(self.to_env_vars().items(), key=lambda kv: kv[0])
        ]
        return "\n".join(parts)

    def resolve_property(
        self, field: ConfigProperty, name: Optional[str] = None, data: DataBag = None
    ) -> Any:
        name = name or field.name
        container = DataBag(data or {})
        value = field.resolve(container, file_path=self.path)
        if name:
            container[name] = value

        if field.fallback_env:
            container[field.fallback_env] = value

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
        fallback_env="REDIS_HOST",
        default_value="localhost",
    )
    SESSION_FILE_DIR = ConfigProperty(
        "session",
        "file_dir",
        fallback_env="SESSION_FILE_DIR",
        default_value="/tmp/",
    )

    REDIS_PORT = ConfigProperty(
        "redis",
        "port",
        fallback_env="REDIS_PORT",
        default_value=6379,
        coerce=int,
    )
    REDIS_DB = ConfigProperty(
        "redis",
        "db",
        fallback_env="REDIS_DB",
        default_value=0,
        coerce=int,
    )
    SECRET_KEY = ConfigProperty(
        "auth",
        "flask_secret",
        fallback_env="SECRET_KEY",
    )
    GITHUB_CLIENT_ID = ConfigProperty(
        "github", "app", "client_id", fallback_env="DRONE_GITHUB_CLIENT_ID"
    )

    GITHUB_CLIENT_SECRET = ConfigProperty(
        "github", "app", "client_secret", fallback_env="DRONE_GITHUB_CLIENT_SECRET"
    )

    SLACK_CLIENT_SECRET = ConfigProperty(
        "slack", "oauth", "client_secret", fallback_env="SLACK_CLIENT_SECRET"
    )

    SLACK_CLIENT_ID = ConfigProperty(
        "slack", "oauth", "client_id", fallback_env="SLACK_CLIENT_ID"
    )

    SLACK_SIGNING_SECRET = ConfigProperty(
        "slack", "oauth", "signing_secret", fallback_env="SLACK_SIGNING_SECRET"
    )

    SLACK_VERIFICATION_TOKEN = ConfigProperty(
        "slack",
        "oauth",
        "verification_token",
        fallback_env="SLACK_VERIFICATION_TOKEN",
    )
    SLACK_BOT_TOKEN = ConfigProperty(
        "slack",
        "oauth",
        "bot_token",
        fallback_env="SLACK_BOT_TOKEN",
    )

    SLACK_APP_USER_TOKEN = ConfigProperty(
        "slack",
        "oauth",
        "app_user_token",
        fallback_env="SLACK_APP_USER_TOKEN",
    )

    sqlalchemy_uri = ConfigProperty(
        "sqlalchemy",
        "uri",
        fallback_env="DRONE_CI_BUTLER_SQLALCHEMY_URI",
    )
    drone_url = ConfigProperty(
        "drone",
        "server",
        fallback_env="DRONE_SERVER_URL",
    )
    drone_access_token = ConfigProperty(
        "drone",
        "access_token",
        fallback_env="DRONE_ACCESS_TOKEN",
    )

    drone_github_owner = ConfigProperty(
        "drone",
        "owner",
        fallback_env="DRONE_GITHUB_OWNER",
    )
    drone_github_repo = ConfigProperty(
        "drone",
        "repo",
        fallback_env="DRONE_GITHUB_REPO",
    )
    auth_jwt_secret = ConfigProperty(
        "auth",
        "jwt_secret",
        fallback_env="DRONE_CI_BUTLER_JWT_SECRET",
    )

    worker_queue_address = ConfigProperty(
        "workers",
        "queue_address",
        fallback_env="DRONE_CI_BUTLER_QUEUE_ADDRESS",
        default_value="tcp://127.0.0.1:5555",
    )

    worker_push_address = ConfigProperty(
        "workers",
        "push_address",
        fallback_env="DRONE_CI_BUTLER_PUSH_ADDRESS",
        default_value="tcp://127.0.0.1:6666",
    )

    worker_pull_address = ConfigProperty(
        "workers",
        "pull_address",
        fallback_env="DRONE_CI_BUTLER_PULL_ADDRESS",
        default_value="tcp://127.0.0.1:7777",
    )

    worker_monitor_address = ConfigProperty(
        "workers",
        "monitor_address",
        fallback_env="DRONE_CI_BUTLER_MONITOR_ADDRESS",
        default_value="tcp://127.0.0.1:5001",
    )

    worker_control_address = ConfigProperty(
        "workers",
        "control_address",
        fallback_env="DRONE_CI_BUTLER_CONTROL_ADDRESS",
        default_value="tcp://127.0.0.1:5002",
    )

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
        p = (
            Path(self.traverse("slack", "store", "installation_path"))
            .expanduser()
            .absolute()
        )
        p.mkdir(exist_ok=True, parents=True)
        return p

    @property
    def slack_state_store_path(self) -> Path:
        p = Path(self.traverse("slack", "store", "state_path")).expanduser().absolute()
        p.mkdir(exist_ok=True, parents=True)
        return p

    def to_flask(self):
        for name in dir(self):
            if name == name.upper():
                try:
                    os.environ[name] = str(getattr(self, name) or "")
                except Exception:
                    pass
        return self


config = Config()
