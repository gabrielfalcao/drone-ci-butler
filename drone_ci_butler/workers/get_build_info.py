import re
from typing import Dict, Optional
from urllib.parse import urlparse
from drone_ci_butler.slack import SlackClient
from drone_ci_butler.drone_api.models import Build
from drone_ci_butler.sql.models.drone import DroneBuild
from drone_ci_butler.sql.models.user import User
from drone_ci_butler.drone_api.models import BuildContext
from drone_ci_butler.rule_engine.default_rules import wf_project_vi
from .puller import PullerWorker


# 1. Poll zmq for job with build_id
# 2. Iterate over failed stages
# 3. For each failed stage check whether a failure notification was already sent
#      otherwise publish zmq event "stage failed" which will store this information in the db to prevent emitting the event twice
# 4. Iterate over pending stages (finished_at == None)
# 5. For each pending stage schedule a new job to monitor build_id
# 6. If the build has all its stages completed with success in all steps
#      then publish zmq event "build succeeded" which will store this information to the db to prevent emitting the event twice

GITHUB_PULL_REQUEST_REGEX = re.compile(
    r"github.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<pr_number>\d+)"
)


def try_parse_github_pull_request_url(url) -> Dict[str, str]:
    parsed = urlparse(url)
    found = GITHUB_PULL_REQUEST_REGEX.search(parsed.path)
    if found:
        return found.groupdict()
    return {}


def try_parse_github_pull_request_number(url) -> Optional[int]:
    return try_parse_github_pull_request_url(url).get("pr_number")


class GetBuildInfoWorker(PullerWorker):
    __log_name__ = "build-info-retriever"

    def process_job(self, info: dict):
        build_id = info.get("build_id")
        ignore_filters = info.get("ignore_filters", False)
        missing_fields = []

        if not build_id:
            missing_fields.append("build_id")

        if missing_fields:
            self.logger.error(f"missing fields: {missing_fields} in job {info}")
            return

        self.logger.debug(f"processing job {info}")
        self.fetch_data(
            self.github_owner, self.github_repo, build_id, ignore_filters=ignore_filters
        )
        self.logger.debug(f"done processing job {info}")

    def fetch_data(
        self, owner: str, repo: str, build_id: int, ignore_filters: bool = False
    ):
        try:
            build = self.api.get_build_info(owner, repo, build_id)
        except Exception as e:
            self.logger.exception(f"failed to retrieve build {owner}/{repo} {build_id}")
            return

        # if the build has been already stored, is not running and has not been updated in postgres then we proceed
        stored = DroneBuild.find_one_by(owner=owner, repo=repo, link=build.link)

        if not ignore_filters:
            if stored and not stored.is_running() and not stored.requires_processing():
                self.logger.warning(
                    f"{build.author_login}'s build ({build.link}) has already been processed and will not be processed: {stored.status}"
                )
                return

        self.logger.info(
            f"storing build {build.number} from {build.link} by {build.author_login}: {build.status}"
        )
        # otherwise we store the build, even if it
        stored = DroneBuild.get_or_create_from_drone_api(
            build.author_login, build.source_repo, build.number, build
        )

        pr_number = try_parse_github_pull_request_number(build.link)
        user = User.find_one_by(github_username=build.author_login)

        self.logger.warning(
            f"{build.number} by {build.author_login}is not a PR: {build.link}"
        )

        if not ignore_filters:
            if not user:
                self.logger.warning(
                    f"ignoring build from a user that has not opted in: {build.author_login}"
                )
                return

            if not pr_number:
                self.logger.warning(
                    f"ignoring build that is not from a Github PR: {build.link} by {repr(build.author_login)}"
                )
                return

            if build.status not in ("running", "failure"):
                self.logger.warning(
                    f"ignoring {build.status} build {build.number} of PR #{pr_number} by {build.author_name}"
                )
                return

        # update the latest build info that includes all its output
        stored.update_from_drone_api(
            owner=owner,
            repo=repo,
            build=build,
        )

        self.process_rulesets(build, stored, user)

    def process_rulesets(self, build: Build, stored: DroneBuild, user: User):
        for stage in build.failed_stages():
            for step in stage.failed_steps():
                context = BuildContext(
                    build=build,
                    stage=stage,
                    step=step,
                )
                self.logger.info(
                    f"processing ruleset {wf_project_vi} against {context}"
                )

                matches = wf_project_vi.apply(context)

                if matches and user:
                    user.notify_ruleset_matches(context, matches)
                    print(message, stage, step, step.to_markdown())

                elif (
                    user
                    and "http-status-check" in str(step.output)
                    and "🖤 404" in str(output.lines)
                ):
                    message = "**http-status-check** failed for {step.to_markdown()}"
                    user.notify_error(message, context, matches)
                    continue
                elif user:
                    self.logger.warning(
                        "no ruleset matches for build {build.number} {build.link} by {build.author_login}"
                    )
