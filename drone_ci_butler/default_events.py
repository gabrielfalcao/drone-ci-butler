from drone_ci_butler.events import http_cache_hit
from drone_ci_butler.events import http_cache_miss
from drone_ci_butler.events import get_build_step_output
from drone_ci_butler.events import get_build_info
from drone_ci_butler.events import get_builds
from drone_ci_butler.events import iter_builds_by_page

from drone_ci_butler.events import user_created
from drone_ci_butler.events import user_updated

from drone_ci_butler.events import token_created
from drone_ci_butler.events import token_updated
from drone_ci_butler.events import github_event


from blinker import signal
from requests import Request, Response
from humanfriendly.text import pluralize

from chemist import Model
from chemist import MODEL_REGISTRY
from drone_ci_butler.logs import get_logger
from drone_ci_butler.sql.models.user import User, AccessToken
from drone_ci_butler.drone_api.models import Build, Stage, Step, Output
from drone_ci_butler.sql.models.drone import DroneBuild
from drone_ci_butler.slack import SlackClient


logger = get_logger("system-events")


def model(name) -> Model:
    Model = MODEL_REGISTRY.get(name)
    if not Model:
        raise KeyError("Model {repr(name)} not declared in {MODEL_REGISTRY}")

    return MODEL_REGISTRY[name]


@github_event.connect
def send_welcome_message_to_slack(flask_app, event, request):
    logger.info(f"Received github event: {event}", request=request)


@token_created.connect
def send_welcome_message_to_slack(flask_app, token: AccessToken, user: User):

    if token.identity_provider != "slack":
        return

    client = SlackClient()
    sent = client.send_message(
        to=user.slack_username,
        text="Github and Slack connected successfully  🎉",
        blocks=[
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Congratulations 🎉",
                    "emoji": True,
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Now that you connected *Github ({user.github_username})* and *Slack* I will watch out for your failed builds with as much useful information as I can.",
                },
            },
        ],
    )
    logger.info(f"Notified user {user} via slack: {sent}")


@http_cache_miss.connect
def log_cache_miss(cache, request: Request, response: Response):
    logger.debug(f"cache miss: {request} {response}")


@http_cache_hit.connect
def log_cache_hit(cache, request: Request, response: Response):
    logger.debug(f"cache hit: {request} {response}")


@get_builds.connect
@iter_builds_by_page.connect
def log_get_builds(
    client,
    owner: str,
    repo: str,
    limit: int,
    page: int,
    builds: Build.List.Type,
    max_builds: int,
    max_pages: int,
):

    count = len(builds)
    logger.debug(
        f'found {pluralize(count, "build")} for {owner}/{repo} page={page} limit={limit}'
    )

    for build in builds:
        stored_build = DroneBuild.get_or_create_from_drone_api(
            owner, repo, build_number=build.number, build=build
        )
        logger.debug(
            f"stored updated build information for build {build.number} {build.link}: {stored_build}"
        )


# @get_build_info.connect
# def log_get_build_info(client, owner: str, repo: str, build_number: int, build: Build):
#     from drone_ci_butler.sql.models.drone import DroneBuild

#     stored_build = DroneBuild.get_or_create_from_drone_api(
#         owner, repo, build_number=build_number, build=build
#     )
#     logger.debug(
#         f"stored updated build information for build {build_number} {build.link}: {stored_build}"
#     )


# @get_build_step_output.connect
# def log_get_build_step_output(
#     client,
#     owner: str,
#     repo: str,
#     build_number: int,
#     stage_number: int,
#     step_number: int,
#     output: Output,
# ):
#     from drone_ci_butler.sql.models.drone import DroneStep

#     stored_step = DroneStep.get_or_create_from_drone_api(
#         owner,
#         repo,
#         build_number=build_number,
#         stage_number=stage_number,
#         step_number=step_number,
#         output=output,
#     )
#     logger.debug(
#         f"stored updated step output {stage_number}/{step_number}: {stored_step}"
#     )
