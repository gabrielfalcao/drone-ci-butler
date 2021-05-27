from blinker import signal
from requests import Request, Response
from humanfriendly.text import pluralize

from drone_ci_butler.logs import get_logger
from drone_ci_butler.drone_api.models import Build, Stage, Step, Output

http_cache_hit = signal("http-cache-hit")
http_cache_miss = signal("http-cache-miss")
get_build_step_output = signal("get-build-step-output")
get_build_info = signal("get-build-info")
get_builds = signal("get-builds")


logger = get_logger("system-events")


@http_cache_miss.connect
def log_cache_miss(cache, request: Request, response: Response):
    logger.debug(f"cache miss: {request} {response}")


@http_cache_hit.connect
def log_cache_hit(cache, request: Request, response: Response):
    logger.debug(f"cache hit: {request} {response}")


@get_builds.connect
def log_get_builds(
    client, owner: str, repo: str, limit: int, page: int, builds: Build.List.Type
):
    count = len(builds)
    logger.debug(
        f'found {pluralize(count, "build")} for {owner}/{repo} page={page} limit={limit}'
    )


@get_build_info.connect
def log_get_build_info(client, owner: str, repo: str, build_id: int, build: Build):
    logger.debug(f"retrieved build {build_id} {build.link}")


@get_build_step_output.connect
def log_get_build_step_output(
    client, owner: str, repo: str, build_id: int, stage: int, step: int, output: Output
):
    logger.debug(f"step output for {build_id}/{stage}/{step} {output}")
