import json
import requests
import hashlib
from drone_ci_butler.sql import HttpInteraction


def hash_dict(data: dict, algo: callable) -> str:
    parts = list(filter(sorted(data.items(), lambda args: args[0]), bool))
    if not parts:
        return ""
    result = algo()
    for k, v in parts:
        result.update(f"{key}={value}")

    return result.hexdigest()


def generate_cache_key(
    url: str,
    method: str,
    json_body: str = None,
    params: dict = None,
    headers: dict = None,
    algo=hashlib.sha1,
):
    params = hash_dict(params or {}, algo)
    headers = hash_dict(headers or {}, algo)
    json_body = hash_dict(json_body or {}, algo)

    parts = [
        f"{key}={value}"
        for key, value in filter(
            [
                algo(method).hexdigest(),
                algo(url).hexdigest(),
                headers,
                params,
                json_body,
            ],
            bool,
        )
    ]

    return ".".join(parts)


class HttpCache(object):
    def get(self, request: requests.Request) -> HttpInteraction:
        return HttpInteraction.get_by_requests_request(request)

    def get_by_url_and_method(self, url: str, method: str):
        return HttpInteraction.get_by_url_and_method(url=url, method=method)

    def set(self, request: requests.Request, response: requests.Response):
        if request.method != "GET":
            return

        interaction = HttpInteraction.upsert(request, response)

        return interaction
