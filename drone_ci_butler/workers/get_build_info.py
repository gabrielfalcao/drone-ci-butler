from drone_ci_butler.slack import SlackClient
from drone_ci_butler.sql.models.drone import DroneBuild
from drone_ci_butler.sql.models.user import User
from .puller import PullerWorker


class GetBuildInfoWorker(PullerWorker):
    __log_name__ = "build-info-retriever"

    def process_job(self, info: dict):
        build_id = info.get("build_id")

        missing_fields = []

        if not build_id:
            missing_fields.append("build_id")

        if missing_fields:
            self.logger.error(f"missing fields: {missing_fields} in {info}")
            return

        self.fetch_data(self.github_owner, self.github_repo, build_id)

    def fetch_data(self, owner: str, repo: str, build_id: int):
        try:
            build = self.api.get_build_info(owner, repo, build_id)
        except Exception as e:
            self.logger.exception(f"failed to retrieve build {owner}/{repo} {build_id}")
            return

        if "/pull" not in (build.link or ""):
            self.logger.debug(
                f"ignoring non pull-request build {build.number} by {build.author_name}"
            )
            return

        pr_number = build.link.split("/")[-1]
        if build.status not in ("running", "failure"):
            self.logger.info(
                f"ignoring {build.status} build {build.number} of PR #{pr_number} by {build.author_name}"
            )
            return

        build = self.api.inject_logs_into_build(owner, repo, build)
        stored = DroneBuild.get_or_create_from_drone_api(
            build.owner, build.repo, build.number, build
        )

        def notify(message, stage, step, output):
            print(message)
            author = User.find_one_by(github_username=build.author_login)
            if not author:
                # ignore builds from github users who did not opt-in
                return

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🔴 Build failed for the PR {pr_number} {owner}/{repo}",
                        "emoji": True,
                    },
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"**Stage:** stage.name"},
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"**Step:** step.name"},
                },
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"```\n{message}\n```"},
                },
                {"type": "divider"},
            ]

            client = SlackClient().slack
            channel = "C023Z62N59Q"
            user_id = "W01BD07TYGP"
            self.logger.info(f"posting message to slack user @falcao")
            message_response = client.chat_postMessage(
                channel=user_id,
                blocks=blocks,
            )

        for stage in build.failed_stages():

            for step in stage.failed_steps():
                error_cause = (
                    lambda cause: f"\033[1;33m{cause} \033[2mcaused failure in {stage.name}.{step.name} (build {build.number}) PR #{pr_number} by {build.author_login}\033[0m"
                )
                real_failure = (
                    lambda cause: f"\033[1;31mReal test failure: \033[2m{cause}\n    in {stage.name}.{step.name} (build {build.number}) PR #{pr_number} by {build.author_login}\033[0m"
                )
                output = step.to_string()
                if "prettier:docs" in output:
                    notify(error_cause(f"Unformatted docs"), stage, step, output)
                    continue
                if "kubectl" in output:
                    notify(error_cause(f"kubernetes deployment"), stage, step, output)
                    continue
                if (
                    "not something we can merge" in output
                    or "Automatic merge failed; fix conflicts" in output
                ):
                    notify(error_cause(f"Merge conflict"), stage, step, output)
                    continue
                if "a DNS-1123 label must consist of lower case" in output:
                    notify(error_cause(f"Invalid branch name"), stage, step, output)
                    continue
                if "yarn lint-ci" in output:
                    notify(error_cause(f"lint"), stage, step, output)
                    continue
                if "bundlesize" in output:
                    notify(error_cause(f"bundlesize is too big"), stage, step, output)
                    continue
                if "ECONNREFUSED" in output:
                    notify(
                        error_cause(f"Network failure (connection refused)"),
                        stage,
                        step,
                        output,
                    )
                    continue
                if "Couldn't find any versions for" in output:
                    notify(
                        error_cause(f"yarn dependency could not be resolved"),
                        stage,
                        step,
                        output,
                    )
                    continue
                if "slack server error" in output:
                    notify(
                        error_cause(f"failed to connect to slack server"),
                        stage,
                        step,
                        output,
                    )
                    continue

                if "http-status-check" in output:
                    for line in step.output.lines:
                        if "🖤 404" in line.out:
                            print(real_failure(line.out))
                    continue

                # print(f"failed step: \033[1;31m{step.to_string()}\033[0m")
                notify(
                    f"failure in {stage.name}.{step.name} of build {build.number} on PR #{pr_number} by {build.author_login}",
                    stage,
                    step,
                    step.to_markdown(),
                )
        # 1. Poll zmq for job with build_id
        # 2. Iterate over failed stages
        # 3. For each failed stage check whether a failure notification was already sent
        #      otherwise publish zmq event "stage failed" which will store this information in the db to prevent emitting the event twice
        # 4. Iterate over pending stages (finished_at == None)
        # 5. For each pending stage schedule a new job to monitor build_id
        # 6. If the build has all its stages completed with success in all steps
        #      then publish zmq event "build succeeded" which will store this information to the db to prevent emitting the event twice
        pass
