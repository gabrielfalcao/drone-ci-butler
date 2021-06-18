from drone_ci_butler.config import config
from sqlalchemy.sql.schema import MetaData

from .models.http import HttpInteraction
from .models.base import context, metadata


def setup_db() -> MetaData:
    return context.set_default_uri(config.sqlalchemy_uri)
