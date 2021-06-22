import logging
from drone_ci_butler.config import config
from sqlalchemy.sql.schema import MetaData
from drone_ci_butler.networking import check_database_dns
from drone_ci_butler.sql.models.http import HttpInteraction
from drone_ci_butler.sql.models.base import context, metadata
from drone_ci_butler.exceptions import UserFriendlyException

logger = logging.getLogger(__name__)


class InvalidDatabaseConfiguration(UserFriendlyException):
    pass


def setup_db() -> MetaData:
    error = check_database_dns()
    if error:
        raise InvalidDatabaseConfiguration(
            f"could not resolve hostname {config.database_hostname!r} from SQLAlchemy URI {config.sqlalchemy_uri}: {error}"
        )

    uri = config.sqlalchemy_uri
    logger.info(f"using sqlalchemy uri: {uri}")
    return context.set_default_uri(uri)
