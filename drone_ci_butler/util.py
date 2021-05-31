import json


def load_json(what, default=None) -> str:
    try:
        return json.loads(what or "{}") or default
    except (json.JSONDecodeError):
        return default
