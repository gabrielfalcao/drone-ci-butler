import os
import yaml
import json
import redis
from typing import Optional
from functools import lru_cache
from pathlib import Path

from uiclasses import DataBag, DataBagChild


class ConfigMissing(Exception):
    def __init__(self, key, filename):
        msg = f"Config key missing {key} in {filename}"
        super().__init__(msg)


class Config(DataBag):
    REDIS_HOST = os.getenv("REDIS_HOST")
    if REDIS_HOST:
        SESSION_TYPE = "redis"
        SESSION_REDIS = redis.Redis(
            host=REDIS_HOST or "localhost",
            port=int(os.getenv("REDIS_PORT") or 6379),
            db=0,
        )
    else:
        SESSION_TYPE = "filesystem"
        SESSION_FILE_DIR = "/tmp/flask-session"

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

    @lru_cache()
    def load(self):
        with self.path.open() as fd:
            return yaml.load(fd, Loader=yaml.FullLoader)

    @property
    def __data__(self):
        return self.load()

    @property
    def sqlalchemy_uri(self) -> str:
        uri = self.traverse("sqlalchemy", "uri")
        if not uri:
            raise ConfigMissing("sqlalchemy.uri", self.path)
        return uri

    @property
    def auth(self) -> DataBagChild:
        return self.traverse("auth")

    @property
    def auth_jwt_secret(self) -> str:
        return self.auth.traverse("jwt_secret")

    @property
    def SECRET_KEY(self) -> str:
        return self.auth.traverse("flask_secret")

    @property
    def slack(self) -> DataBagChild:
        return self.traverse("slack")

    @property
    def slack_oauth(self) -> DataBagChild:
        oauth = self.slack.traverse("oauth")
        if not oauth:
            raise ConfigMissing("slack.oauth", self.path)
        return oauth

    @property
    def SLACK_CLIENT_SECRET(self) -> Optional[str]:
        return self.slack_oauth["client_secret"]

    @property
    def SLACK_CLIENT_ID(self) -> Optional[str]:
        return self.slack_oauth["client_id"]

    @property
    def SLACK_SIGNING_SECRET(self) -> Optional[str]:
        return self.slack_oauth["signing_secret"]

    @property
    def SLACK_VERIFICATION_TOKEN(self) -> Optional[str]:
        return self.slack_oauth["verification_token"]

    @property
    def GITHUB_AUTHORIZE_PARAMS(self) -> dict:
        return {}  # {"scope": "repo user read:user user:email"}

    @property
    def GITHUB_CLIENT_ID(self) -> str:
        return self.traverse("github", "app", "client_id")

    @property
    def GITHUB_CLIENT_SECRET(self) -> str:
        return self.traverse("github", "app", "client_secret")

    @property
    def SLACK_BOT_TOKEN(self) -> Optional[str]:
        return self.slack_oauth["bot_token"]

    @property
    def SLACK_APP_USER_TOKEN(self) -> Optional[str]:
        return self.slack_oauth["app_user_token"]

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
