import os
from typing import Optional, List, Any, Dict
from pathlib import Path
from uiclasses import UserFriendlyObject, DataBag
from drone_ci_butler.util import load_yaml, load_json
from drone_ci_butler.exceptions import ConfigMissing


class ConfigProperty(UserFriendlyObject):
    name: str
    path: List[str]
    fallback_env: str
    default_value: Any
    deserialize: callable

    def __init__(self, *path: List[str], **kw):
        name = kw.pop("name", None)
        fallback_env = kw.pop("fallback_env", None)
        default_value = kw.pop("default_value", None)

        deserialize = kw.pop("deserialize", None)
        if deserialize:
            self.deserialize = deserialize
        else:
            self.deserialize = lambda x: x

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

        if not value and self.fallback_env:
            value = os.getenv(self.fallback_env)

        if not value and self.path:
            value = config.traverse(*self.path)

        if not value and self.default_value is not None:
            value = self.default_value

        if value is None:
            raise ConfigMissing(
                attr,
                file_path,
                self.fallback_env,
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
