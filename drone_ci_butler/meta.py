import os
from typing import Optional, List, Any, Dict
from pathlib import Path
from uiclasses import UserFriendlyObject, DataBag
from drone_ci_butler.util import load_yaml, load_json
from drone_ci_butler.exceptions import ConfigMissing


class ConfigProperty(UserFriendlyObject):
    name: str
    path: List[str]
    env: str
    default_value: Any
    deserialize: callable

    def __init__(self, *path: List[str], **kw):
        name = kw.pop("name", None)
        env = kw.pop("env", None)
        default_value = kw.pop("default_value", None)

        deserialize = kw.pop("deserialize", None)
        if deserialize:
            self.deserialize = deserialize
        else:
            self.deserialize = lambda x: x

        if not path and not env:
            raise SyntaxError(
                f"ConfigProperty requires at least one path name, or a env keyword-arg"
            )
        for k, v in dict(
            name=name or env,
            path=list(path),
            env=env,
            default_value=default_value,
            **kw,
        ).items():
            setattr(self, k, v)

    def resolve(self, config: DataBag, file_path: Optional[Path]):
        name = self.name or self.env
        attr = ".".join(self.path)
        value = None

        if not value and self.env:
            value = os.getenv(self.env)

        if not value and self.path:
            value = config.traverse(*self.path)

        if not value and self.default_value is not None:
            value = self.default_value

        if value is None:
            raise ConfigMissing(
                attr,
                file_path,
                self.env,
            )

        try:
            return self.deserialize(value)
        except Exception as e:
            logger.warning(
                f"failed to deserialize value {value} with {self.deserialize}: {e}"
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
