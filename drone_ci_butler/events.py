from blinker import signal
from requests import Request, Response
from humanfriendly.text import pluralize

from drone_ci_butler.logs import get_logger
from drone_ci_butler.sql.models import DroneBuild, DroneStep
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
    stored_build = DroneBuild.get_or_create_from_drone_api(owner, repo, build)
    logger.debug(
        f"stored updated build information for build {build_id} {build.link}: {stored_build}"
    )


@get_build_step_output.connect
def log_get_build_step_output(
    client,
    owner: str,
    repo: str,
    build_number: int,
    stage_number: int,
    step_number: int,
    output: Output,
):

    stored_step = DroneStep.get_or_create_from_drone_api(
        owner,
        repo,
        build_number=build_number,
        stage_number=stage_number,
        step_number=step_number,
        output=output,
    )
    logger.debug(
        f"stored updated step output {stage_number}/{step_number}: {stored_step}"
    )
