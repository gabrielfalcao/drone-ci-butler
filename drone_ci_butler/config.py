import os
import yaml
from functools import lru_cache
from pathlib import Path
from uiclasses import DataBag, DataBagChild


class Config(DataBag):
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
    def auth(self) -> DataBagChild:
        return self.traverse("auth")

    @property
    def auth_jwt_secret(self) -> DataBagChild:
        return self.auth.traverse("jwt_secret")

    @property
    def slack(self) -> DataBagChild:
        return self.traverse("slack")

    @property
    def slack_oauth(self) -> DataBagChild:
        return self.slack.traverse("oauth")

    @property
    def slack_client_secret(self) -> Optional[str]:
        return self.slack_oauth["client_secret"]

    @property
    def slack_client_id(self) -> Optional[str]:
        return self.slack_oauth["client_id"]

    @property
    def slack_signing_secret(self) -> Optional[str]:
        return self.slack_oauth["signing_secret"]

    @property
    def slack_verification_token(self) -> Optional[str]:
        return self.slack_oauth["verification_token"]

    @property
    def slack_bot_token(self) -> Optional[str]:
        return self.slack_oauth["bot_token"]


config = Config()
