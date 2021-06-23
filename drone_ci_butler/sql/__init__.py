import logging
from pathlib import Path

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from sqlalchemy.sql.schema import MetaData
from sqlalchemy.engine.base import Engine
from drone_ci_butler.config import Config
from drone_ci_butler.config import config
from drone_ci_butler.exceptions import UserFriendlyException
from drone_ci_butler.networking import check_database_dns
from drone_ci_butler.sql.models.base import context, metadata
from drone_ci_butler.sql.models.http import HttpInteraction


logger = logging.getLogger(__name__)
alembic_ini_path = Path(__file__).parent.parent.joinpath("alembic.ini").absolute()


class InvalidDatabaseConfiguration(UserFriendlyException):
    pass


def check_dns():
    error = check_database_dns()
    if error:
        raise InvalidDatabaseConfiguration(
            f"could not resolve hostname {config.database_hostname!r} from SQLAlchemy URI {config.sqlalchemy_uri}: {error}"
        )


def setup_db(config: Config) -> Engine:
    check_dns()
    uri = config.sqlalchemy_uri
    logger.info(f"using sqlalchemy uri: {uri}")
    context.set_default_uri(uri)
    return context.get_default_engine()


def migrate_db(config: Config, target: str = "head"):
    setup_db(config)

    script_location = str(alembic_ini_path.parent.joinpath("migrations"))
    sqlalchemy_uri = config.sqlalchemy_uri
    alembic_cfg = AlembicConfig(str(alembic_ini_path))
    alembic_cfg.set_section_option("alembic", "sqlalchemy.url", sqlalchemy_uri)
    alembic_cfg.set_section_option(
        "alembic",
        "script_location",
        script_location,
    )
    logger.info(
        f"running database migrations against {alembic_ini_path}",
        extra=dict(
            alembic_ini_path=str(alembic_ini_path),
            script_location=script_location,
            database_hostname=config.database_hostname,
            database_port=config.database_port,
        ),
    )
    alembic_command.upgrade(alembic_cfg, target)
