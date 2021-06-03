import os
import yaml
from functools import lru_cache
from pathlib import Path


class Config(object):
    def __init__(self, path=None):
        self.path = (
            Path(
                path
                or os.getenv("DRONE_CI_BUTLER_CONFIG_PATH")
                or "~/.drone-ci-butler.yml"
            )
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
    def slack(self):
        return self.__data__.get("slack") or {}

    @property
    def slack_oauth(self):
        return self.slack["oauth"]

    @property
    def slack_client_secret(self):
        return self.slack_oauth["client_secret"]

    @property
    def slack_client_id(self):
        return self.slack_oauth["client_id"]

    @property
    def slack_signing_secret(self):
        return self.slack_oauth["signing_secret"]

    @property
    def slack_verification_token(self):
        return self.slack_oauth["verification_token"]

    @property
    def slack_bot_token(self):
        return self.slack_oauth["bot_token"]


config = Config()
