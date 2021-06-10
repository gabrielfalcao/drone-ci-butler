from blinker import signal
from requests import Request, Response
from humanfriendly.text import pluralize

from drone_ci_butler.logs import get_logger
from drone_ci_butler.sql.models.drone import DroneBuild, DroneStep
from drone_ci_butler.sql.models.user import User, AccessToken
from drone_ci_butler.drone_api.models import Build, Stage, Step, Output

http_cache_hit = signal("http-cache-hit")
http_cache_miss = signal("http-cache-miss")
get_build_step_output = signal("get-build-step-output")
get_build_info = signal("get-build-info")
get_builds = signal("get-builds")

user_created = signal("user-created")
user_updated = signal("user-updated")

token_created = signal("token-created")
token_updated = signal("token-updated")
github_event = signal("github-event")


logger = get_logger("system-events")


@github_event.connect
def send_welcome_message_to_slack(flask_app, event, request):
    logger.info(f"Received github event: {event}", request=request)


@token_created.connect
def send_welcome_message_to_slack(flask_app, token: AccessToken, user: User):
    from drone_ci_butler.slack import SlackClient

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
def log_get_builds(
    client, owner: str, repo: str, limit: int, page: int, builds: Build.List.Type
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


@get_build_info.connect
def log_get_build_info(client, owner: str, repo: str, build_number: int, build: Build):
    stored_build = DroneBuild.get_or_create_from_drone_api(
        owner, repo, build_number=build_number, build=build
    )
    logger.debug(
        f"stored updated build information for build {build_number} {build.link}: {stored_build}"
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
