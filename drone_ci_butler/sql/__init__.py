import logging
from drone_ci_butler.config import config
from sqlalchemy.sql.schema import MetaData

from .models.http import HttpInteraction
from .models.base import context, metadata

logger = logging.getLogger(__name__)


def setup_db() -> MetaData:
    uri = config.sqlalchemy_uri
    logger.info(f"using sqlalchemy uri: {uri}")
    return context.set_default_uri(uri)
