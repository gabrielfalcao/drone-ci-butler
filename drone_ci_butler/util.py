import json
import yaml
from pathlib import Path
from drone_ci_butler.logs import get_logger

logger = get_logger(__name__)


def load_json(what, default=None) -> str:
    try:
        return json.loads(what or "{}") or default
    except (json.JSONDecodeError):
        return default


def load_yaml(path: Path) -> dict:
    try:
        path = path.expanduser().absolute()
        with path.open() as fd:
            return yaml.load(fd, Loader=yaml.FullLoader)
    except Exception as e:
        logger.warning(f"failed to load path {path}: {e}")
        return {}
