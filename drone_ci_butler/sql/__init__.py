from .models.http import HttpInteraction
from .models.base import context, metadata
from drone_ci_butler.config import config


def setup_db():
    context.set_default_uri(config.sqlalchemy_uri)
